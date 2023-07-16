from app.alarm.sender import AlarmSender


def test_exclude_unsubscribers():
    # given
    subscribers: list[str] = ["subscriber1", "subscriber2", "subscriber3"]
    unsubscribers: set[str] = {"subscriber1", "subscriber2"}
    # when
    excluded = AlarmSender._exclude_unsubscribers(subscribers, unsubscribers)
    # then
    assert isinstance(excluded, set)
    assert excluded == {"subscriber3"}


def test_chunk_subscribers():
    # given
    subscribers: list[str] = ["subscriber" for _ in range(5)]
    max_concurrent: int = 2
    # when
    chunked = AlarmSender._chunk_subscribers(subscribers, max_concurrent)
    # then
    assert len(chunked) == 3
