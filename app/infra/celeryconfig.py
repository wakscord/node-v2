from datetime import timedelta

from app.common.settings import settings

timezone = "Asia/Seoul"

broker_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_URL}"
result_backend = broker_url
result_expires = timedelta(hours=1)

broker_connection_retry_on_startup = True
result_backend_thread_safe = True
