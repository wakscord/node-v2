from app.alarm.sender import AlarmService


def test_chunk_subscribers():
    # given
    subscribers: list[str] = ["subscriber" for _ in range(5)]
    max_concurrent: int = 2
    # when
    chunked = AlarmService._chunk_subscribers(subscribers, max_concurrent)
    # then
    assert len(chunked) == 3
