"""
VADP — Unit Tests for Secrets Management Subsystem
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from app.core.secrets import (
    AWSSecretsManagerProvider,
    EnvSecretsProvider,
    HashiCorpVaultProvider,
    SecretsFactory,
)


class TestSecretsManagement(unittest.TestCase):

    def setUp(self):
        os.environ["SECRETS_PROVIDER"] = "env"
        os.environ["TEST_SECRET_KEY"] = "secret_value_123"

    def test_env_secrets_provider(self):
        provider = EnvSecretsProvider()
        self.assertTrue(provider.health_check())
        self.assertEqual(provider.get_secret("TEST_SECRET_KEY"), "secret_value_123")
        self.assertEqual(provider.get_secret("NON_EXISTENT_KEY", "default"), "default")

    def test_secrets_factory_env(self):
        os.environ["SECRETS_PROVIDER"] = "env"
        provider = SecretsFactory.get_provider(force_reload=True)
        self.assertIsInstance(provider, EnvSecretsProvider)

    def test_aws_secrets_manager_provider(self):
        mock_client_instance = MagicMock()
        mock_client_instance.get_secret_value.return_value = {
            "SecretString": '{"DB_PASS": "aws_db_password", "API_KEY": "aws_api_key"}'
        }

        provider = AWSSecretsManagerProvider(secret_name="test/secret", cache_ttl_seconds=60)
        provider._client = mock_client_instance

        self.assertEqual(provider.get_secret("DB_PASS"), "aws_db_password")
        self.assertEqual(provider.get_secret("API_KEY"), "aws_api_key")

    def test_vault_secrets_provider(self):
        mock_client_instance = MagicMock()
        mock_client_instance.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"DB_PASS": "vault_db_password"}}
        }

        provider = HashiCorpVaultProvider(vault_token="test-token", cache_ttl_seconds=60)
        provider._client = mock_client_instance

        self.assertEqual(provider.get_secret("DB_PASS"), "vault_db_password")


if __name__ == "__main__":
    unittest.main()
