"""
Hardware Security Module (HSM) PKCS#11 Signing Provider for VADP
===================================================================

Provides PKCS#11 compliant Hardware Security Module (HSM) integration
(YubiHSM2 / AWS CloudHSM / SoftHSM2) for hardware-isolated NIST P-256 ECDSA
key pair generation, digital contract signing, and key slot management.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

logger = logging.getLogger(__name__)


class HSMProvider:
    """
    PKCS#11 Hardware Security Module & Cloud KMS signing provider.
    Supports hardware key isolation (AWS CloudHSM / AWS KMS / YubiHSM2 / SoftHSM2) with software fallback.
    """

    def __init__(
        self,
        pkcs11_lib_path: Optional[str] = None,
        token_label: str = "VADP_JUDICIAL_HSM_TOKEN",
        user_pin: str = "1234",
        key_label: str = "vadp_ecdsa_p256_root_key",
        kms_key_id: Optional[str] = None,
    ):
        self.pkcs11_lib_path = pkcs11_lib_path or os.getenv(
            "PKCS11_LIB_PATH", "/usr/lib/softhsm/libsofthsm2.so"
        )
        self.token_label = token_label
        self.user_pin = user_pin
        self.key_label = key_label
        self.kms_key_id = kms_key_id or os.getenv("AWS_KMS_KEY_ID")
        self.is_hsm_active = False
        self.is_kms_active = False
        self._fallback_key: Optional[ec.EllipticCurvePrivateKey] = None
        self._fallback_key_path: Path = (
            Path(__file__).resolve().parent.parent.parent
            / "signing_keys"
            / "ledger_key.pem"
        )

        self._initialize_hsm()

    def _initialize_hsm(self) -> None:
        """Attempt Cloud KMS / PKCS#11 library loading or fall back to software isolated key."""
        # 1. Try AWS KMS
        if self.kms_key_id:
            try:
                import boto3  # type: ignore

                self.kms_client = boto3.client("kms")
                self.is_kms_active = True
                logger.info(
                    f"Initialized Cloud KMS Hardware Key Provider with KeyId: {self.kms_key_id}"
                )
                return
            except Exception as e:
                logger.warning(
                    f"Cloud KMS initialization failed ({e}); checking PKCS#11."
                )

        # 2. Try PKCS#11 shared library
        try:
            import PyKCS11  # type: ignore

            if os.path.exists(self.pkcs11_lib_path):
                self.pkcs11 = PyKCS11.PyKCS11Lib()
                self.pkcs11.load(self.pkcs11_lib_path)
                self.is_hsm_active = True
                logger.info(
                    f"Initialized Hardware Security Module via PKCS#11: {self.pkcs11_lib_path}"
                )
                return
        except Exception as e:
            logger.warning(
                f"PKCS#11 HSM library initialization failed ({e}); engaging software isolated SECP256R1 key fallback."
            )

        self.is_hsm_active = False
        self.is_kms_active = False
        self._fallback_key = self._load_or_create_fallback_key()

    def _load_or_create_fallback_key(self) -> ec.EllipticCurvePrivateKey:
        """Load persistent ECDSA P-256 key from disk, or generate and persist one."""
        key_path = self._fallback_key_path
        if key_path.exists():
            try:
                pem_bytes = key_path.read_bytes()
                loaded = serialization.load_pem_private_key(pem_bytes, password=None)
                if isinstance(loaded, ec.EllipticCurvePrivateKey):
                    logger.debug(
                        f"Loaded persistent ECDSA fallback key from {key_path}"
                    )
                    return loaded
            except Exception as e:
                logger.warning(
                    f"Failed to load ledger_key.pem ({e}); generating new key."
                )
        # Generate and persist a new key
        new_key = ec.generate_private_key(ec.SECP256R1())
        key_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.write_bytes(
            new_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        logger.info(f"Generated and persisted new ECDSA fallback key at {key_path}")
        return new_key

    def sign_digest(self, digest_sha256: bytes) -> bytes:
        """
        Signs 32-byte digest using NIST P-256 ECDSA key on Cloud KMS, hardware HSM, or fallback key.
        """
        if self.is_kms_active:
            try:
                response = self.kms_client.sign(
                    KeyId=self.kms_key_id,
                    Message=digest_sha256,
                    MessageType="DIGEST",
                    SigningAlgorithm="ECDSA_SHA_256",
                )
                return bytes(response["Signature"])
            except Exception as ex:
                logger.error(
                    f"Cloud KMS sign failed ({ex}); attempting HSM/software fallback."
                )

        if self.is_hsm_active:
            try:
                session = self.pkcs11.openSession(0)
                session.login(self.user_pin)
                key_obj = session.findObjects(
                    [
                        (PyKCS11.CKA_LABEL, self.key_label),
                        (PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY),
                    ]
                )[0]
                mech = PyKCS11.Mechanism(PyKCS11.CKM_ECDSA, None)
                signature = bytes(session.sign(key_obj, digest_sha256, mech))
                session.logout()
                session.closeSession()
                return signature
            except Exception as ex:
                logger.error(
                    f"HSM PKCS#11 hardware sign failed ({ex}); falling back to software key."
                )

        # Software key fallback
        assert self._fallback_key is not None
        return self._fallback_key.sign(digest_sha256, ec.ECDSA(hashes.SHA256()))

    def get_public_key_pem(self) -> str:
        """Retrieve public key in SubjectPublicKeyInfo PEM format."""
        if self.is_kms_active:
            try:
                response = self.kms_client.get_public_key(KeyId=self.kms_key_id)
                pub_der = response["PublicKey"]
                pub_key = serialization.load_der_public_key(pub_der)
                return pub_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                ).decode("utf-8")
            except Exception:
                pass

        if self.is_hsm_active:
            try:
                session = self.pkcs11.openSession(0)
                key_obj = session.findObjects(
                    [
                        (PyKCS11.CKA_LABEL, self.key_label),
                        (PyKCS11.CKA_CLASS, PyKCS11.CKO_PUBLIC_KEY),
                    ]
                )[0]
                pub_bytes = bytes(key_obj.getAttributeValue([PyKCS11.CKA_EC_POINT])[0])
                session.closeSession()
            except Exception:
                pass

        assert self._fallback_key is not None
        return (
            self._fallback_key.public_key()
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode("utf-8")
        )


# Default global instance
default_hsm_provider = HSMProvider()
