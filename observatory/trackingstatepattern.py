import abc
import json
import re
import warnings
from os import path
from time import time
from uuid import uuid4

import requests
from observatory import settings
from observatory.constants import LABEL_PATTERN

def start_run(model, version, mode, experiment='default'):
    """
    Starts a new run for a specific model version.

    You can use this function start start recording data related to a single experiment run.
    The use of experiments is optional, you can leave this parameter out. See the example below for basic usage.

    >>> with observatory.start_run('my_model', 1, remote, experiment='my_experiment') as run:
    >>>     # Record metrics, outputs and settings

    A new run is created on the server at the start of the scope.
    It is automatically finalized at the end of the scope.

    Note that when an exception occurs within the scope of a run,
    the run is automatically marked as failed.

    Each time you invoke `start_run()` a new run is created with a newly generated UUID.
    This ensures that no runs overlap eachother.

    **Please note** it is not possible to resume a run that you started earlier.

    Parameters
    ----------
    model : string
        The name of the model
    version : int
        The version number of the model
    experiment : string, optional
        The experiment you're working on
    """

    if model is None or model.strip() == '':
        raise AssertionError('Please provide a name for your model.')

    if not re.match(LABEL_PATTERN, model):
        raise AssertionError('name is invalid. It can contain ' +
                             'lower-case alpha-numeric characters and dashes only.')

    if experiment is None:
        experiment = 'default'

    if experiment != 'default':
        if experiment.strip() == '' or not re.match(LABEL_PATTERN, experiment):
            raise AssertionError('experiment is invalid. It can contain ' +
                                 'lower-case alpha-numeric characters and dashes only.')

    if version <= 0:
        raise AssertionError('version must be greater than zero')

    if mode == "local":
        state = LocalState()
    elif mode == "remote":
        state = RemoteState()
    else:
        raise AssertionError('Given mode is not valid, it must me "local" or "remote".')

    run_id = str(uuid4())
    #tracking_client = TrackingClient(settings.server_url)

    #return TrackingSession(model, version, experiment, run_id, tracking_client)
    return TrackingSession(model, version, experiment, run_id, state)


class TrackingSession:
    #trackingsession

    def __init__(self, name, version, experiment, run_id, state):
        """
        Initializes the tracking session with the necessary tracking information
        and a pre-initialized tracking client for recording the actual metrics.

        Parameters
        ----------
        name : string
            Name of the model
        version : int
            Version number of the model
        experiment : string
            Name of the experiment
        run_id : string
            ID of the run
        state : object
            Instance of the current state
        """
        self.name = name
        self.version = version
        self.experiment = experiment
        self.run_id = run_id
        self._state = state

    def record_metric(self, name, value):
        """
        Records a metric value on the server

        Parameters
        ----------
        name : string
            The name of the metric to record
        value : float
            The value of the metric to records
        """

        # Typechecking in python is a no-go under normal circumstances.
        # But here we're using it, because the server expects a string and float.

        if name is None or type(name) != str or name.strip() == '':
            raise AssertionError('Please provide a valid name for the metric.')

        if not re.match(LABEL_PATTERN, name):
            raise AssertionError(
                'Please provide a valid name for the metric.' +
                'it can contain lower-case alpha-numeric characters and dashes only.')

        if value is None or (type(value) != float and type(value) != int):
            raise AssertionError(
                'Please provide a valid value for the metric.')

        response = self._state.record_metric(
            self.name, self.version, self.experiment, self.run_id, name, value)

        self._verify_response(response, 201)

    def record_settings(self, **settings):
        """
        Records settings used for the run

        Parameters
        ----------
        settings : object
            A dictionary containing all settings used for the run.
            This can be passed in as `key=value` pairs.
        """
        
        if settings is None:
            warnings.warn(
                'Trying to record empty settings. ' + 
                'To prevent risk of settings loss on the server, ' +
                'the empty settings collection is discarded.', 
                RuntimeWarning)

        response = self._state.record_settings(
            self.name, self.version, self.experiment,
            self.run_id, dict(settings))

        self._verify_response(response, 201)

    def record_output(self, input_file, filename):
        """
        Records an output for the current run.

        Parameters
        ----------
        input_file : object
            Filename or handle to input file
        filename : string
            Name of the file as it should be stored on the server
        """

        if filename is None or filename.strip() == '':
            raise AssertionError(
                'Please provide a valid filename to store the output on the server.')

        if input_file is None or input_file.strip() == '':
            raise AssertionError(
                'Please provide a valid filename for input_file.')

        absolute_file_path = path.abspath(input_file)

        if not path.exists(absolute_file_path):
            raise AssertionError(
                f'Could not find source file {absolute_file_path} ' +
                'to upload as output of this run. Please make ' +
                'sure that the file exists on disk.')

        response = self._state.record_output(
            self.name, self.version, self.experiment,
            self.run_id, filename, open(absolute_file_path))

        self._verify_response(response, 201)

    def __enter__(self):
        print('name: ' + self.name)
        print('version: ' + str(self.version))
        print('experiment: ' + self.experiment)
        print('run_id: ' + self.run_id)
        response = self._state.record_session_start(
            self.name, self.version, self.experiment, self.run_id)

        self._verify_response(response, 201)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            session_status = 'COMPLETED'
        else:
            session_status = 'FAILED'

        response = self._state.record_session_end(
            self.name, self.version, self.experiment,
            self.run_id, session_status)

        self._verify_response(response, 201)

        return exc_type is None

    def _verify_response(self, response, expected_status, expected_type='application/json'):
        """
        Verifies the response received from the tracking client against the expected status code.
        Also verifies that the method contains valid data according to the expected content_type.

        Use this method whenever your receive data from the server, to make sure that the contents
        are readable as expected.
        """
        actual_status = response.status_code
        actual_type = response.headers['Content-Type']

        if response.status_code != expected_status:
            try:
                response_content = response.json()
                error_message = response_content['message']

                raise RuntimeError('Failed to execute operation. Server returned ' +
                                   f'an error with status {actual_status}: {error_message}')
            except:
                # In some weird cases the server returns an error nobody will ever understand.
                # This catch-all fixes the problem and returns a somewhat useful error message.
                raise RuntimeError('Failed to execute operation. Server returned ' +
                                   f'an error with status: {actual_status}')

        # Sometimes the server does respond, but sends some weird piece of data that we can't parse.
        # This check makes sure that we don't try to ever read it.
        if actual_type != expected_type:
            raise RuntimeError(f'Failed to execute operation. ' +
                               'Received invalid response type: {actual_type}')


class ObservatoryState(abc.ABCMeta):

    @abc.abstractmethod
    def record_metric(self, name, value):
        """
        This method will record a metric.
        """
        pass

    @abc.abstractmethod
    def record_settings():
        """
        This method will record a setting.
        """
        pass

    @abc.abstractmethod
    def record_output():
        """
        This method will record a output.
        """
        pass

    @abc.abstractmethod
    def record_session_start(self, model, version, experiment, run_id):
        """
        This method will record the start of a run.
        """
        pass

    @abc.abstractmethod
    def record_session_end(self, model, version, experiment, run_id, status):
        """
        This method will record the end of a run.
        """
        pass

class LocalState(ObservatoryState):
    #Handels metrics for the local filesystem -> Sind.py

    def record_metric(self, model, version, experiment, run_id, name, value):
        #sink.save_metric(model, version, experiment, run_id, name, value)
        #localstate is nothing more than a nice data handler that passes is to sink.py
        #this is because the sever is also going to use sink.py to save data
        print("LocalState : record_metric")

    def record_settings():
        print("LocalState : record_settings")

    def record_output():
        print("LocalState : record_output")

    def record_session_start(self, model, version, experiment, run_id):
        """
        Records the start of a session.

        This method sends a HTTP request with the right payload to the observatory tracking endpoint.
        The result is a 201 when the server succesfully recorded the session completion. Otherwise
        the server will return a 500 response.

        Parameters:
        -----------
        model : str
            The name of the model
        version : int
            The version of the model
        experiment : str
            The name of the experiment
        run_id : str
            The identifier for the run
        print("LocalState : record_session_start")
        """

    def record_session_end(self, model, version, experiment, run_id, status):
        print("LocalState : record_session_end")


class RemoteState(ObservatoryState):
    #Handels metrics for the remote endpoint

    def record_metric(self, model, version, experiment, run_id, name, value):
        """
        Records a metric during a run.

        This method sends a HTTP request with the right payload to the observatory tracking endpoint.
        The result is a 201 when the server succesfully recorded the session completion. Otherwise
        the server will return a 500 response.

        Parameters:
        -----------
        model : str
            The name of the model
        version : int
            The version of the model
        experiment : str
            The name of the experiment
        run_id : str
            The identifier for the run
        metric_name : str
            The name of the metric
        metric_value : str
            The value of the metric

        Returns:
        --------
        requests.Response
            The response from the server
        """
        handler_url = f'{settings.server_url}/api/models/{model}/versions/{version}/experiments/{experiment}/runs/{run_id}/metrics'
        return requests.post(handler_url, json={'name': metric_name, 'value': metric_value})

    def record_settings():
        print("RemoteState : record_settings")
        """
        Records the settings of an experiment run.

        This method sends a HTTP request with the right payload to the observatory tracking endpoint.
        The result is a 201 when the server succesfully recorded the session completion. Otherwise
        the server will return a 500 response.

        Parameters:
        -----------
        model : str
            The name of the model
        version : int
            The version of the model
        experiment : str
            The name of the experiment
        run_id : str
            The identifier for the run
        settings : dict
            The dictionary with run settings

        Returns:
        --------
        requests.Response
            The response from the server
        """
        handler_url = f'{settings.server_url}/api/models/{model}/versions/{version}/experiments/{experiment}/runs/{run_id}/settings'
        return requests.post(handler_url, json=settings)


    def record_output():
        print("RemoteState : record_output")
        """
        Records an output of an experiment run

        This method sends a HTTP request with the right payload to the observatory tracking endpoint.
        The result is a 201 when the server succesfully recorded the session completion. Otherwise
        the server will return a 500 response.

        Parameters:
        -----------
        model : str
            The name of the model
        version : int
            The version of the model
        experiment : str
            The name of the experiment
        run_id : str
            The identifier for the run
        filename : str
            The filename of the output
        file : object
            The file handle to use for reading the output data

        Returns:
        --------
        requests.Response
            The response from the server
        """
        handler_url = f'{settings.server_url}/api/models/{model}/versions/{version}/experiments/{experiment}/runs/{run_id}/outputs/{filename}'

        file_collection = {
            'file': (filename, file, 'application/octet-stream')
        }

        return requests.put(handler_url, files=file_collection)

    def record_session_start(self, model, version, experiment, run_id):
        """
        Records the start of a session.

        This method sends a HTTP request with the right payload to the observatory tracking endpoint.
        The result is a 201 when the server succesfully recorded the session completion. Otherwise
        the server will return a 500 response.

        Parameters:
        -----------
        model : str
            The name of the model
        version : int
            The version of the model
        experiment : str
            The name of the experiment
        run_id : str
            The identifier for the run

        Returns:
        --------
        requests.Response
            The response from the server
        """
        handler_url = f'{settings.server_url}/api/models/{model}/versions/{version}/experiments/{experiment}/runs'
        return requests.post(handler_url, json={'run_id': run_id})

    def record_session_end(self, model, version, experiment, run_id, status):
        """
        Records the end of a session.

        This method sends a HTTP request with the right payload to the observatory tracking endpoint.
        The result is a 201 when the server succesfully recorded the session completion. Otherwise
        the server will return a 500 response.

        Parameters:
        -----------
        model : str
            The name of the model
        version : int
            The version of the model
        experiment : str
            The name of the experiment
        run_id : str
            The identifier for the run
        status : str
            The status of the run

        Returns:
        --------
        requests.Response
            The response from the server
        """
        handler_url = f'{settings.server_url}/api/models/{model}/versions/{version}/experiments/{experiment}/runs/{run_id}'
        return requests.put(handler_url, json={'status': status})
        
