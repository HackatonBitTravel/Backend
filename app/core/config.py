# Fichier de configuration centrale de l'application
# Charge les variables d'environnement et les rend accessibles partout

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str
    DEBUG: bool
    API_VERSION: str
    DATABASE_URL: str
    SECRET_KEY: str
    KKIAPAY_PUBLIC_KEY: str
    KKIAPAY_PRIVATE_KEY: str
    KKIAPAY_SECRET: str
    KKIAPAY_SANDBOX: bool = True
    BTCPAY_URL: str = ""
    BTCPAY_API_KEY: str = ""
    BTCPAY_STORE_ID: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
