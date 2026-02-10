from redis import Redis
from core.config import RedisSettings

def get_redis_connection() -> Redis:
    print(RedisSettings.REDIS_HOST)
    client = Redis(host=RedisSettings.REDIS_HOST, port=RedisSettings.REDIS_PORT)
    return client