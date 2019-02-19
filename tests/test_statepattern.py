import json
import os
from tempfile import mkstemp

from observatory.trackingstatepattern import TrackingSession, start_run, LocalState, RemoteState
from observatory.constants import LABEL_PATTERN
from observatory.server import run_server
from hypothesis import example, given, strategies, assume
import requests
import requests.exceptions
import pytest

INVALID_LABELS = ['test!', 'TEst', 'Test', 'Test 123', '', '  ', 'test!']

@pytest.fixture()
def run_output():
    """
    This fixture produces a default output file of a run with some data in it.
    You can use this whenever you need to record an output of a run
    """
    _, file_path = mkstemp(suffix='.txt')

    with open(file_path, 'w') as test_file:
        test_file.write('test')

    yield file_path

    try:
        os.remove(file_path)
    except:
        pass

@pytest.mark.parametrize('model', INVALID_LABELS)
def test_start_run_with_invalid_model(model):
    with pytest.raises(AssertionError):
        try:
            with start_run(model, 1):
                pass
        except requests.exceptions.ConnectionError:
            pass

@pytest.mark.parametrize('experiment', INVALID_LABELS)
def test_start_run_with_invalid_experiment(experiment):
    with pytest.raises(AssertionError):
        try:
            with start_run('test', 1, experiment=experiment):
                pass
        except requests.exceptions.ConnectionError:
            pass

def test_start_run_with_invalid_version():
    with pytest.raises(AssertionError):
        try:
            with start_run('test', 0):
                pass
        except requests.exceptions.ConnectionError:
            pass

def test_session_scope_behavior():
    #this does nothing, fix this
    with TrackingSession('test', 1, 'test', 'test') as run:
     run.change(LocalState)

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
        session.change(LocalState)
        session.record_metric(metric_name, metric_value)

# FIX connention to a server first, otherwise this will always fail.
#@given(
#    metric_name=strategies.from_regex(LABEL_PATTERN),
#    metric_value=strategies.floats(min_value=0.0, max_value=10.000)
#)
#def test_record_metrics_remote(metric_name, metric_value):
#    """
#    You can record metrics during your run.
#    The number of times doesn't matter, we record all of them.
#    """
#    assume(metric_name.strip() != '')
#    assume(metric_name != None)
#
#    with TrackingSession('test', 1, 'test', 'test') as session:
#        session.change(RemoteState)
#        session.record_metric(metric_name, metric_value)

@pytest.mark.parametrize('metric_name', INVALID_LABELS)
def test_record_metric_with_invalid_name(metric_name):
    with pytest.raises(AssertionError):
        with TrackingSession('test', 1, 'test', 'test') as session:
            session.change(LocalState)
            session.record_metric(metric_name, 1.0)

def test_record_metric_without_value():
    with pytest.raises(AssertionError):
        with TrackingSession('test', 1, 'test', 'test') as session:
            session.change(LocalState)
            session.record_metric('test', None)

def test_record_metric_with_invalid_value():
    with pytest.raises(AssertionError):
        with TrackingSession('test', 1, 'test', 'test') as session:
            session.change(LocalState)
            session.record_metric('test', 'invalid')

def test_record_metric_with_invalid_name_pattern():
    with pytest.raises(AssertionError):
        with TrackingSession('test', 1, 'test', 'test') as session:
            session.change(LocalState)
            session.record_metric('test space', 'invalid')

def test_record_metric_with_invalid_name_type():
    with pytest.raises(AssertionError):
        with TrackingSession('test', 1, 'test', 'test') as session:
            session.change(LocalState)
            session.record_metric(1.0, 'invalid')

def test_record_output(run_output):
    with TrackingSession('test', 1, 'test', 'test') as session:
        session.change(LocalState)
        session.record_output(run_output, 'test.txt')

def test_record_output_with_empty_filename(run_output):
    with pytest.raises(AssertionError):
        with TrackingSession('test', 1, 'test', 'test') as session:
            session.change(LocalState)
            session.record_output(run_output, None)

def test_record_output_with_empty_source_file():
    with pytest.raises(AssertionError):
        with TrackingSession('test', 1, 'test', 'test') as session:
            session.change(LocalState)
            session.record_output(None, 'test.txt')

def test_record_output_with_non_existing_file():
    with pytest.raises(AssertionError):
        with TrackingSession('test', 1, 'test', 'test') as session:
            session.change(LocalState)
            session.record_output('test2.txt', 'test.txt')

def test_record_settings():
    with TrackingSession('test', 1, 'test', 'test') as session:
        session.change(LocalState)
        session.record_settings(test='value')

def test_record_settings_without_keys():
    with TrackingSession('test', 1, 'test', 'test') as session:
        session.change(LocalState)
        session.record_settings()
