from pydantic_settings import BaseSettings


class Configs(BaseSettings):
    DB_ENGINE: str
    DB_USER: str
    DB_PW: str
    DB_HOST: str
    DB_PORT: str
    DATA_BASE: str

    class Config:
        env_file = ".env"

    @property
    def DATABASE_URL(self):
        return f"{self.DB_ENGINE}://{self.DB_USER}:{self.DB_PW}@{self.DB_HOST}:{self.DB_PORT}/{self.DATA_BASE}"
