import json
import os
from tempfile import mkstemp

import pytest
import requests
import requests.exceptions
from hypothesis import example, given, strategies, assume
from observatory.constants import LABEL_PATTERN
from observatory.tracking import TrackingClient, TrackingSession, start_run

INVALID_LABELS = ['test!', 'TEst', 'Test', 'Test 123', '', '  ', 'test!']


@pytest.fixture()
def mock_client(mocker):
    """
    This fixture produces a mock tracking client that returns default responses
    for all operations executed. You can change its behavior afterwards if you need to.
    """
    fake_headers = {'Content-Type': 'application/json'}

    mock_response = mocker.Mock(
        requests.Response, status_code=201, headers=fake_headers)

    client = mocker.Mock(TrackingClient)

    client.record_metric.return_value = mock_response
    client.record_output.return_value = mock_response
    client.record_settings.return_value = mock_response
    client.record_session_end.return_value = mock_response
    client.record_session_start.return_value = mock_response

    return client


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
    """
    You cannot start a run with an invalid model.
    """
    with pytest.raises(AssertionError):
        try:
            with start_run(model, 1):
                pass
        except requests.exceptions.ConnectionError:
            pass


@pytest.mark.parametrize('experiment', INVALID_LABELS)
def test_start_run_with_invalid_experiment(experiment):
    """
    You cannot start a run with an invalid experiment
    """
    with pytest.raises(AssertionError):
        try:
            with start_run('test', 1, experiment=experiment):
                pass
        except requests.exceptions.ConnectionError:
            pass

def test_start_run_with_invalid_version():
    """
    You cannot start a run with an invalid experiment
    """
    with pytest.raises(AssertionError):
        try:
            with start_run('test', 0):
                pass
        except requests.exceptions.ConnectionError:
            pass


def test_session_scope_behavior(mock_client):
    """
    Everytime you start a new tracking session the start is recorded.
    Also, everytime a session ends, that is recorded as well.
    """
    with TrackingSession('test', 1, 'test', 'test', mock_client):
        pass

    mock_client.record_session_start.assert_called()
    mock_client.record_session_end.assert_called()


@given(
    metric_name=strategies.from_regex(LABEL_PATTERN),
    metric_value=strategies.floats(min_value=0.0, max_value=10.000)
)
def test_record_metrics(mock_client, metric_name, metric_value):
    """
    You can record metrics during your run.
    The number of times doesn't matter, we record all of them.
    """
    assume(metric_name.strip() != '')
    assume(metric_name != None)

    with TrackingSession('test', 1, 'test', 'test', mock_client) as session:
        session.record_metric(metric_name, metric_value)

    mock_client.record_metric.assert_called()


@pytest.mark.parametrize('metric_name', INVALID_LABELS)
def test_record_metric_with_invalid_name(mock_client, metric_name):
    """
    You cannot record metrics without a name.
    """
    with pytest.raises(AssertionError):
        with TrackingSession('test', 1, 'test', 'test', mock_client) as session:
            session.record_metric(metric_name, 1.0)


def test_record_metric_without_value(mock_client):
    """
    You can't record metrics without a value
    """
    with pytest.raises(AssertionError):
        with TrackingSession('test', 1, 'test', 'test', mock_client) as session:
            session.record_metric('test', None)


def test_record_metric_with_invalid_value(mock_client):
    """
    You can't record metrics with values other than ints or floats.
    """
    with pytest.raises(AssertionError):
        with TrackingSession('test', 1, 'test', 'test', mock_client) as session:
            session.record_metric('test', 'blaa')


def test_record_metric_with_invalid_name_pattern(mock_client):
    """
    You can't record metrics that have characters in the name 
    other than lower-case alphanumeric characters and dashes.
    """
    with pytest.raises(AssertionError):
        with TrackingSession('test', 1, 'test', 'test', mock_client) as session:
            session.record_metric('test hooray', 'blaa')


def test_record_metric_with_invalid_name_type(mock_client):
    """
    You can't record metrics with a non-string name
    """
    with pytest.raises(AssertionError):
        with TrackingSession('test', 1, 'test', 'test', mock_client) as session:
            session.record_metric(1.0, 'blaa')


def test_record_output(mock_client, run_output):
    """
    You can record outputs of existing files with a custom filename
    """
    with TrackingSession('test', 1, 'test', 'test', mock_client) as session:
        session.record_output(run_output, 'test.txt')

    mock_client.record_output.assert_called()


def test_record_output_with_empty_filename(run_output, mock_client):
    """
    You cannot record outputs without specifying a name
    """
    with pytest.raises(AssertionError):
        with TrackingSession('test', 1, 'test', 'test', mock_client) as session:
            session.record_output(run_output, None)


def test_record_output_with_empty_source_file(mock_client):
    """
    You cannot record outputs without specifying a source path
    """
    with pytest.raises(AssertionError):
        with TrackingSession('test', 1, 'test', 'test', mock_client) as session:
            session.record_output(None, 'test.txt')


def test_record_output_with_non_existing_file(mock_client):
    """
    You cannot record outputs without specifying an existing file
    """
    with pytest.raises(AssertionError):
        with TrackingSession('test', 1, 'test', 'test', mock_client) as session:
            session.record_output('test2.txt', 'test.txt')


def test_record_settings(mock_client):
    with TrackingSession('test', 1, 'test', 'test', mock_client) as session:
        session.record_settings(test='value')

    mock_client.record_settings.assert_called()


def test_record_settings_without_keys(mock_client):
    with TrackingSession('test', 1, 'test', 'test', mock_client) as session:
        session.record_settings()

    mock_client.record_settings.assert_called()

