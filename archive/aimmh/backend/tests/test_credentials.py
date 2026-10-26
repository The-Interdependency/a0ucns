import os


def env_value(name: str, default: str) -> str:
    return os.getenv(name, default)


TEST_USER_PASSWORD = env_value("TEST_USER_PASSWORD", "test123456")
TEST_USER_ALT_PASSWORD = env_value("TEST_USER_ALT_PASSWORD", "testpass123")
TEST_USER_WRONG_PASSWORD = env_value("TEST_USER_WRONG_PASSWORD", "wrongpassword")
TEST_AUTH_STRONG_PASSWORD = env_value("TEST_AUTH_STRONG_PASSWORD", "SecurePass123!")

TEST_SERVICE_ACCOUNT_PASSWORD = env_value("TEST_SERVICE_ACCOUNT_PASSWORD", "botpass123")
TEST_SERVICE_ACCOUNT_ALT_PASSWORD = env_value("TEST_SERVICE_ACCOUNT_ALT_PASSWORD", "bot_password_123")
TEST_SHORT_PASSWORD = env_value("TEST_SHORT_PASSWORD", "pass123")
TEST_SHORT_ALT_PASSWORD = env_value("TEST_SHORT_ALT_PASSWORD", "pass456")

TEST_FAKE_API_KEY = env_value("TEST_FAKE_API_KEY", "test-api-key-xyz")
