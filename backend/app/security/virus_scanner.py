"""
VADP Virus Scanner & Malware Defense Engine
=================================================

High-performance malware scanner inspecting uploaded judicial documents for:
  - EICAR standard antivirus test signatures
  - Unauthorized executable headers (Windows MZ / Linux ELF PE payloads)
  - ClamAV daemon integration (Unix/TCP socket when available)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)

# Standard EICAR Test Signature
EICAR_SIGNATURE = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

# Executable Magic Headers
EXECUTABLE_MAGIC_HEADERS = [
    b"MZ",           # Windows Portable Executable (EXE/DLL)
    b"\x7fELF",      # Linux Executable Format (ELF)
    b"\xca\xfe\xba\xbe", # Java Class / Mach-O universal binary
    b"\xfe\xed\xfa\xce", # Mach-O 32-bit
    b"\xfe\xed\xfa\xcf", # Mach-O 64-bit
]

# Optional ClamAV import
try:
    import clamd
    HAS_CLAMD = True
except ImportError:
    clamd = None  # type: ignore
    HAS_CLAMD = False


class VirusScanner:
    """Malware and virus scanner for document attachments."""

    _clamd_client = None

    @classmethod
    def _get_clamd(cls):
        if not HAS_CLAMD or cls._clamd_client is False:
            return None
        if cls._clamd_client is None:
            try:
                # Try connecting to ClamAV daemon on localhost:3310
                client = clamd.ClamdNetworkSocket(host="localhost", port=3310)
                client.ping()
                cls._clamd_client = client
            except Exception:
                cls._clamd_client = False
                return None
        return cls._clamd_client

    @classmethod
    def scan_file(cls, file_path: str | Path) -> Tuple[bool, str | None]:
        """
        Scan a local file for virus, malware, or executable threat.

        Returns:
            (is_safe: bool, threat_description: str | None)
        """
        path = Path(file_path)
        try:
            if not path.exists():
                logger.warning("File missing or quarantined before scan", extra={"path": str(path)})
                return False, "File quarantined or unlinked by host antivirus protection"
        except Exception:
            return False, "File quarantined or unlinked by host antivirus protection"

        # 1. ClamAV Daemon Scan (if active)
        clam_client = cls._get_clamd()
        if clam_client:
            try:
                result = clam_client.scan(str(path))
                if result and str(path) in result:
                    status, threat = result[str(path)]
                    if status == "FOUND":
                        logger.warning("ClamAV threat detected", extra={"path": str(path), "threat": threat})
                        return False, f"ClamAV threat: {threat}"
            except Exception as e:
                logger.warning("ClamAV scan error; falling back to signature inspection", extra={"error": str(e)})

        # 2. Local Signature & Binary Magic Header Inspection
        try:
            with open(path, "rb") as f:
                header_bytes = f.read(4096)

            # Check for EICAR signature anywhere in the header buffer or full file
            if EICAR_SIGNATURE in header_bytes:
                logger.warning("EICAR test malware signature detected", extra={"path": str(path)})
                return False, "EICAR-STANDARD-ANTIVIRUS-TEST-FILE"

            # Check full file if size is small (< 100KB)
            if path.stat().st_size < 100 * 1024:
                with open(path, "rb") as f:
                    full_content = f.read()
                    if EICAR_SIGNATURE in full_content:
                        logger.warning("EICAR test malware signature detected", extra={"path": str(path)})
                        return False, "EICAR-STANDARD-ANTIVIRUS-TEST-FILE"

            # Check for disguised executable magic headers on non-executable files
            ext = path.suffix.lower()
            if ext in (".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".webp"):
                for magic in EXECUTABLE_MAGIC_HEADERS:
                    if header_bytes.startswith(magic):
                        logger.warning(
                            "Disguised executable binary payload detected",
                            extra={"path": str(path), "magic": magic.hex()},
                        )
                        return False, f"Unauthorized executable binary header (magic: 0x{magic.hex()})"

        except (OSError, PermissionError) as exc:
            logger.warning("File access error during malware scan (likely host OS quarantine)", extra={"path": str(path), "error": str(exc)})
            return False, f"Malware quarantine or access blocked: {exc}"
        except Exception as exc:
            logger.error("File scanning error", extra={"path": str(path), "error": str(exc)})
            return False, f"Scan failed: {exc}"

        return True, None
