# ============================================================
# VADP Backend — Secrets Management Subsystem
# ============================================================
# Unified abstraction providing dynamic, encrypted secret fetching
# from AWS Secrets Manager, HashiCorp Vault, or local environment fallback.
# Includes memory caching with TTL, health checking, and key rotation support.
# ============================================================

from abc import ABC, abstractmethod
import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)


class BaseSecretsProvider(ABC):
    """Abstract base class for all secret management backends."""

    def __init__(self, cache_ttl_seconds: int = 300) -> None:
        self.cache_ttl = cache_ttl_seconds
        self._cache: dict[str, Any] = {}
        self._cache_timestamp: float = 0.0

    @abstractmethod
    def get_secret(self, key: str, default: str | None = None) -> str | None:
        """Retrieve a specific secret value by key."""
        pass

    @abstractmethod
    def get_secret_dict(self, secret_name: str | None = None) -> dict[str, Any]:
        """Retrieve all key-value secrets as a dictionary."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verify secret provider connectivity and health."""
        pass

    def clear_cache(self) -> None:
        """Invalidate the local secrets cache."""
        self._cache.clear()
        self._cache_timestamp = 0.0

    def _is_cache_valid(self) -> bool:
        return bool(self._cache) and (time.time() - self._cache_timestamp) < self.cache_ttl


class EnvSecretsProvider(BaseSecretsProvider):
    """Environment variables & local .env secret provider."""

    def get_secret(self, key: str, default: str | None = None) -> str | None:
        return os.getenv(key, default)

    def get_secret_dict(self, secret_name: str | None = None) -> dict[str, Any]:
        return dict(os.environ)

    def health_check(self) -> bool:
        return True


class AWSSecretsManagerProvider(BaseSecretsProvider):
    """AWS Secrets Manager provider using boto3."""

    def __init__(
        self,
        secret_name: str | None = None,
        region_name: str | None = None,
        cache_ttl_seconds: int = 300,
    ) -> None:
        super().__init__(cache_ttl_seconds=cache_ttl_seconds)
        self.secret_name = secret_name or os.getenv("AWS_SECRET_NAME", "VADP/production")
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import boto3

                self._client = boto3.client(
                    service_name="secretsmanager", region_name=self.region_name
                )
            except Exception as e:
                logger.warning(f"Failed to initialize AWS SecretsManager client: {e}")
                self._client = None
        return self._client

    def get_secret_dict(self, secret_name: str | None = None) -> dict[str, Any]:
        if self._is_cache_valid():
            return self._cache

        target = secret_name or self.secret_name
        client = self._get_client()
        if not client:
            return {}

        try:
            response = client.get_secret_value(SecretId=target)
            if "SecretString" in response:
                secret_data = json.loads(response["SecretString"])
            else:
                secret_data = {}

            self._cache = secret_data
            self._cache_timestamp = time.time()
            return secret_data
        except Exception as e:
            logger.error(f"AWS Secrets Manager error retrieving '{target}': {e}")
            return self._cache or {}

    def get_secret(self, key: str, default: str | None = None) -> str | None:
        secrets = self.get_secret_dict()
        return str(secrets.get(key, default)) if key in secrets else os.getenv(key, default)

    def health_check(self) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            client.describe_secret(SecretId=self.secret_name)
            return True
        except Exception:
            return False


class HashiCorpVaultProvider(BaseSecretsProvider):
    """HashiCorp Vault provider supporting KV v1/v2 engines."""

    def __init__(
        self,
        vault_url: str | None = None,
        vault_token: str | None = None,
        secret_path: str | None = None,
        mount_point: str = "secret",
        cache_ttl_seconds: int = 300,
    ) -> None:
        super().__init__(cache_ttl_seconds=cache_ttl_seconds)
        self.vault_url = vault_url or os.getenv("VAULT_ADDR", "http://localhost:8200")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN", "")
        self.secret_path = secret_path or os.getenv("VAULT_SECRET_PATH", "VADP/config")
        self.mount_point = mount_point or os.getenv("VAULT_MOUNT_POINT", "secret")
        self._client = None

    def _get_client(self):
        if self._client is None and self.vault_token:
            try:
                import hvac

                self._client = hvac.Client(url=self.vault_url, token=self.vault_token)
            except Exception as e:
                logger.warning(f"Failed to initialize HashiCorp Vault client: {e}")
                self._client = None
        return self._client

    def get_secret_dict(self, secret_name: str | None = None) -> dict[str, Any]:
        if self._is_cache_valid():
            return self._cache

        target_path = secret_name or self.secret_path
        client = self._get_client()
        if not client:
            return {}

        try:
            # Try KV v2 read
            read_response = client.secrets.kv.v2.read_secret_version(
                path=target_path, mount_point=self.mount_point
            )
            secret_data = read_response.get("data", {}).get("data", {})
            self._cache = secret_data
            self._cache_timestamp = time.time()
            return secret_data
        except Exception as e:
            logger.debug(f"KV v2 read failed for '{target_path}', attempting fallback: {e}")
            try:
                # KV v1 fallback
                read_response = client.secrets.kv.v1.read_secret(
                    path=target_path, mount_point=self.mount_point
                )
                secret_data = read_response.get("data", {})
                self._cache = secret_data
                self._cache_timestamp = time.time()
                return secret_data
            except Exception as ex:
                logger.error(f"HashiCorp Vault read error for '{target_path}': {ex}")
                return self._cache or {}

    def get_secret(self, key: str, default: str | None = None) -> str | None:
        secrets = self.get_secret_dict()
        return str(secrets.get(key, default)) if key in secrets else os.getenv(key, default)

    def health_check(self) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            return client.is_authenticated()
        except Exception:
            return False


class SecretsFactory:
    """Factory for selecting and instantiating secret management providers."""

    _instance: BaseSecretsProvider | None = None

    @classmethod
    def get_provider(cls, force_reload: bool = False) -> BaseSecretsProvider:
        if cls._instance is not None and not force_reload:
            return cls._instance

        provider_type = os.getenv("SECRETS_PROVIDER", "env").lower()

        if provider_type == "aws":
            logger.info("Initializing AWS Secrets Manager Provider")
            cls._instance = AWSSecretsManagerProvider()
        elif provider_type == "vault":
            logger.info("Initializing HashiCorp Vault Provider")
            cls._instance = HashiCorpVaultProvider()
        elif provider_type == "auto":
            # Try AWS -> Vault -> Env
            aws_provider = AWSSecretsManagerProvider()
            if aws_provider.health_check():
                logger.info("Auto-selected AWS Secrets Manager Provider")
                cls._instance = aws_provider
            else:
                vault_provider = HashiCorpVaultProvider()
                if vault_provider.health_check():
                    logger.info("Auto-selected HashiCorp Vault Provider")
                    cls._instance = vault_provider
                else:
                    logger.info("Auto-selected Environment Secrets Provider")
                    cls._instance = EnvSecretsProvider()
        else:
            logger.info("Initializing Environment Secrets Provider")
            cls._instance = EnvSecretsProvider()

        return cls._instance


# Convenience global accessor
def get_secret(key: str, default: str | None = None) -> str | None:
    return SecretsFactory.get_provider().get_secret(key, default)
