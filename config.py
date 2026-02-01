from pydantic_settings import BaseSettings, SettingsConfigDict

class DatabaseSettings(BaseSettings):
    URL: str = ...
    ECHO: bool = False

    model_config = SettingsConfigDict(env_file='.env', env_prefix="DB_", extra="ignore")

class ADBSettings(BaseSettings):
    PATH: str = ...
    SCRCPY_SERVER_PATH: str = ...
    DEVICE_SERVER_PATH: str = ...

    model_config = SettingsConfigDict(env_file='.env', env_prefix="ADB_", extra="ignore")

db_config = DatabaseSettings()
adb_config = ADBSettings()