import httpx
import orjson
from celery import Task, shared_task
from httpx._models import Response
from redis import Redis

from app.alarm.exceptions import RateLimitException
from app.alarm.result_parser import DEFAULT_RETRY_AFTER, UNSUBSCRIBERS_KEY, AlarmResultParser
from app.infra.redis import session


class AlarmSender:
    @classmethod
    def send(cls, session: Redis, subscribers: list[str], message: dict) -> None:
        # 구독 해제 유저들 제외
        unsubscribers: set[str] = session.smembers(UNSUBSCRIBERS_KEY)
        active_subscribers = cls._exclude_unsubscribers(subscribers=subscribers, unsubscribers=unsubscribers)

        for subscriber in active_subscribers:
            send_alarm.delay(key=subscriber, message=message)

    @staticmethod
    def _exclude_unsubscribers(subscribers: list[str], unsubscribers: list[bytes]) -> set[str]:
        return set(subscribers) - {unsubscriber.decode("utf-8") for unsubscriber in unsubscribers}


@shared_task(bind=True)
def send_alarm(self: Task, key: str, message: dict) -> None:
    try:
        headers = {"Content-Type": "application/json"}
        url = f"https://discord.com/api/webhooks/{key}"

        response: Response = httpx.post(url=url, data=orjson.dumps(message), headers=headers)
        AlarmResultParser(session=session).parse(key=key, result=response)

    except RateLimitException as exc:
        raise self.retry(exc=exc, countdown=exc.retry_after, max_retries=10)

    except Exception as exc:
        raise self.retry(exc=str(exc), countdown=DEFAULT_RETRY_AFTER, max_retries=10)
