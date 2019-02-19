import json
import os
from tempfile import mkstemp

from observatory.trackingstatepattern import TrackingSession, start_run, LocalState, RemoteState
from observatory.constants import LABEL_PATTERN
from hypothesis import example, given, strategies, assume
import requests
import requests.exceptions
import pytest


@given(
    metric_name=strategies.from_regex(LABEL_PATTERN),
    metric_value=strategies.floats(min_value=0.0, max_value=10.000)
)
def test_record_metrics_local(metric_name, metric_value):
    """
    You can record metrics during your run.
    The number of times doesn't matter, we record all of them.
    """
    assume(metric_name.strip() != '')
    assume(metric_name != None)

    with TrackingSession('test', 1, 'test', 'test') as session:
        session.change(LocalState())
        session.record_metric(metric_name, metric_value)

    session.record_metric.assert_called()

@given(
    metric_name=strategies.from_regex(LABEL_PATTERN),
    metric_value=strategies.floats(min_value=0.0, max_value=10.000)
)
def test_record_metrics_remote(metric_name, metric_value):
    """
    You can record metrics during your run.
    The number of times doesn't matter, we record all of them.
    """
    assume(metric_name.strip() != '')
    assume(metric_name != None)

    with TrackingSession('test', 1, 'test', 'test') as session:
        session.change(RemoteState())
        session.record_metric(metric_name, metric_value)

    session.record_metric.assert_called()
