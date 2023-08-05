import json

import pytest

from app.common.utils.exceptions import ParseInvalidArgumentException, ParseInvalidFormatException
from app.common.utils.task_parser import AlarmTask, TaskParser


def test_parse_raw_task():
    # given
    keys = ["test"]
    data = {"message": "test"}

    request = json.dumps({"keys": keys, "data": data})
    raw_task = ("node", str(request))

    # when
    result: AlarmTask = TaskParser._parse_raw_task(raw_task=raw_task)

    # then
    assert result.keys == keys and result.data == data


def test_parse_raw_task_failed_format_invalid():
    # given
    keys = ["test"]
    data = {"message": "test"}

    request = json.dumps({"invalid_keys": keys, "invalid_data": data})
    raw_task = ("node", str(request))

    # when
    with pytest.raises(ParseInvalidFormatException):
        # then
        TaskParser._parse_raw_task(raw_task=raw_task)


def test_parse_validate_empty():
    # given
    category = "subscribers"
    # when
    with pytest.raises(ParseInvalidArgumentException) as exc:
        TaskParser._validate_empty(data=None, category=category)
    # then
    assert f"{category} is empty" in str(exc.value)


def test_parse_subscribers():
    # given
    keys = ["test"]
    data = {"message": "test"}

    request = json.dumps({"keys": keys, "data": data})
    raw_task = ("node", str(request))

    # when
    subscribers = TaskParser(raw_task=raw_task).parse_subscribers()

    # then
    assert subscribers == keys


def test_parse_message():
    # given
    keys = ["test"]
    data = {"message": "test"}

    request = json.dumps({"keys": keys, "data": data})
    raw_task = ("node", str(request))

    # when
    message = TaskParser(raw_task=raw_task).parse_message()

    # then
    assert message == data
