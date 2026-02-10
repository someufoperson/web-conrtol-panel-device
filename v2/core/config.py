from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

class DatabaseSettings(Config):
    DB_URL: str
    ECHO: bool

class ADBSettings(Config):
    ADB_PATH: str
    SCRCPY_SERVER_PATH: str
    DEVICE_SERVER_PATH: str

class RedisSettings(Config):
    REDIS_HOST: str
    REDIS_PORT: int

class TGBotSettings(Config):
    TG_BOT_TOKEN: str
    ADMIN_ID: int

class LinkSettings(Config):
    LINK: str


db_settings = DatabaseSettings()
adb_settings = ADBSettings()
redis_settings = RedisSettings()
tg_bot_settings = TGBotSettings()
link_settings = LinkSettings()