from redis import Redis

from app.common.settings import settings

session = Redis(host=settings.REDIS_URL, port=6379, password=settings.REDIS_PASSWORD)
