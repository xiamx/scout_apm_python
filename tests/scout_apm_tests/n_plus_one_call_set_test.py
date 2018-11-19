from __future__ import absolute_import, division, print_function, unicode_literals

from scout_apm.core.n_plus_one_call_set import NPlusOneCallSet, NPlusOneCallSetItem


def test_call_set_finds_or_creates():
    sql = "SELECT * from test"
    callset = NPlusOneCallSet()
    assert 0 == len(callset.items)
    item = callset.find_for(sql)
    assert 1 == len(callset.items)
    assert item.sql_string == sql


def test_call_set_updates():
    sql = "SELECT * from test"
    callset = NPlusOneCallSet()
    callset.update(sql, 3, 4)
    item = callset.find_for(sql)
    assert 3 == item.call_count
    assert 4 == item.call_duration


def test_should_capture_backtrace():
    sql = "SELECT * from test"
    callset = NPlusOneCallSet()
    callset.update(
        sql,
        NPlusOneCallSetItem.CALL_COUNT_THRESHOLD - 1,
        NPlusOneCallSetItem.DURATION_THRESHOLD - 1,
    )
    assert not callset.should_capture_backtrace(sql)
    callset.update(sql, 1, 1)
    assert callset.should_capture_backtrace(sql)


def test_no_capture_if_already_captured():
    sql = "SELECT * from test"
    callset = NPlusOneCallSet()
    callset.update(
        sql,
        NPlusOneCallSetItem.CALL_COUNT_THRESHOLD,
        NPlusOneCallSetItem.DURATION_THRESHOLD,
    )
    assert callset.should_capture_backtrace(sql)
    # Subsequent calls should return False
    assert not callset.should_capture_backtrace(sql)
    callset.update(sql, 1, 1)
    assert not callset.should_capture_backtrace(sql)


def test_is_past_duration_threshold():
    sql = "SELECT * from test"
    callset = NPlusOneCallSet()
    callset.update(sql, 0, NPlusOneCallSetItem.DURATION_THRESHOLD - 1)
    item = callset.find_for(sql)
    assert not item.is_past_duration_threshold()
    callset.update(sql, 0, 1)
    assert item.is_past_duration_threshold()
    # Assert again to test the attribute check in the function
    assert item.is_past_duration_threshold()
