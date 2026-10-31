import pytest

from retrykit import RetryError, retry


def flaky(fail_times, exc=ValueError):
    state = {"calls": 0}

    def fn():
        state["calls"] += 1
        if state["calls"] <= fail_times:
            raise exc("boom")
        return "ok"

    return fn, state


def test_succeeds_after_failures():
    fn, state = flaky(2)
    assert retry(attempts=3, sleep=lambda _: None)(fn)() == "ok"
    assert state["calls"] == 3


def test_raises_retry_error_with_cause():
    fn, _ = flaky(10)
    with pytest.raises(RetryError) as info:
        retry(attempts=2, sleep=lambda _: None)(fn)()
    assert isinstance(info.value.__cause__, ValueError)
    assert info.value.attempts == 2


def test_unlisted_exceptions_propagate_immediately():
    fn, state = flaky(1, exc=KeyError)
    with pytest.raises(KeyError):
        retry(attempts=5, exceptions=(ValueError,), sleep=lambda _: None)(fn)()
    assert state["calls"] == 1


def test_backoff_delays_without_jitter():
    delays = []
    fn, _ = flaky(3)
    retry(attempts=4, base_delay=1, factor=2, max_delay=3, jitter=0, sleep=delays.append)(fn)()
    assert delays == [1, 2, 3]


def test_on_retry_hook_and_metadata_preserved():
    seen = []
    fn, _ = flaky(1)

    @retry(attempts=2, sleep=lambda _: None, on_retry=lambda n, e, d: seen.append(n))
    def wrapped():
        """doc"""
        return fn()

    assert wrapped() == "ok" and seen == [1]
    assert wrapped.__name__ == "wrapped" and wrapped.__doc__ == "doc"


def test_rejects_zero_attempts():
    with pytest.raises(ValueError):
        retry(attempts=0)
