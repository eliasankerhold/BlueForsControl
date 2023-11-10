from .base import Mode, ADMIN_MODE, OPERATOR_MODE, LEAD_MODE, FOLLOW_MODE, UNAUTHENTICATED_MODE
from .error_handling import (InsufficientPermissionException, CommunicationError, DeviceError, EmptyValueError,
                             ValueNotSynchronizedWarning)
from .event_logger import bfc_logger

import requests


class BlueFClient:
    def __init__(self, ip: str, mode: Mode, api_key: str = None, port: int = 49098, num_channels: int = 12,
                 num_heaters: int = 12):
        self.ip = ip
        self.port = port
        self.mode = mode
        self.__protocol = 'https://'
        self.NUM_CHANNELS = num_channels
        self.NUM_HEATERS = num_heaters

        assert ip != ' '

        if api_key is None:
            self.__api_key = 'unauthenticated'

        else:
            self.__api_key = api_key

        self.__compatible_api_versions = ['v2.2']
        self.system_name, self.system_version, self.api_version = self.system_info()

        if self.api_version not in self.__compatible_api_versions:
            bfc_logger.warning(f"Incompatible API version. System API version {self.api_version} is not in list of"
                               f" compatible versions ({self.__compatible_api_versions}). "
                               f"Proceeding with execution, but crashes and unexpected behavior will likely occur.")

    def __check_permission(self, required_permission: int):
        """
        Checks if the permission of the caller is sufficient to execute the operation. Serves as a filter on client side
        to prevent permission error in server response. The actual access control is enforced on the server side through
        API key management.

        :param required_permission: Level of permission required for the operation.
        :type required_permission: int
        :raises InsufficientPermissionException: If the permission of the caller is insufficient for the operation.
        """
        if self.mode.permission > required_permission:
            raise InsufficientPermissionException(required_permission, self.mode.permission)

    def __make_endpoint(self, *args):
        """
        Turns arguments into server endpoint with https://ip:port/ as basis.

        :param args: Path components to endpoint.
        :type args: str
        :return: Endpoint address.
        :rtype: str
        """
        bfc_logger.debug(f'Created endpoint: https://{self.ip}:{self.port}' + '/' + '/'.join(args))
        return f'{self.__protocol}{self.ip}:{self.port}' + '/' + '/'.join(args)

    @staticmethod
    def __hide_key(url_string: str):
        """
        Replaces the api key in an url or text with * for secure logging.

        :param url_string: String containing api key preceded by ?key=
        :type url_string: str
        :return: Cleared string where the key has been replaced with *
        :rtype: str
        """
        if '?key=' in url_string:
            parts = url_string.split('?key=')
            if ' ' in parts[1]:
                split_char = ' '

            else:
                split_char = '?'

            other_params = parts[1].split(split_char)
            hidden_key = ''.rjust(len(other_params[0]), '*')
            safe_endpoint = parts[0] + '?key=' + hidden_key + split_char.join(other_params[1:])

            return safe_endpoint

    def __generic_request(self, path: str, params: dict = None, payload: dict = None):
        """
        Handles a generic https request with query parameters and optional payload. If payload is provided, it is passed
        as JSON in a POST request. Otherwise, a GET request is sent.

        :param params: HTTP query parameters. API key will always be added by default.
        :type params: dict
        :param path: Path to server endpoint.
        :type path: str
        :param payload: Data to be passed along in POST request.
        :type payload: dict
        :return: JSON response parsed to dictionary.
        :rtype: dict
        """
        try:
            if params is None:
                params = {'key': self.__api_key}

            else:
                params['key'] = self.__api_key

            if payload is None:
                req = requests.Request(url=path, params=params, method='GET')
                prepared = req.prepare()
                bfc_logger.debug(f"{prepared.method} {self.__hide_key(prepared.url)}")
                response = requests.Session().send(prepared)

            else:
                req = requests.Request(url=path, params=params, method='POST', data=payload)
                prepared = req.prepare()
                bfc_logger.debug(f"{prepared.method} {self.__hide_key(prepared.url)} with payload {prepared.body}")
                response = requests.Session().send(prepared)

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.InvalidURL,
                requests.exceptions.MissingSchema) as ex:
            return {'status': 'ERROR', 'code': -1, 'description': self.__hide_key(str(ex)),
                    'endpoint': path}

        try:
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as ex:
            return {'status': 'ERROR', 'code': -1, 'description': self.__hide_key(str(ex)),
                    'endpoint': self.__hide_key(response.url)}

    @staticmethod
    def __json_check(response_json: dict):
        """
        Checks JSON data returned by the control software for an erroneous response.

        :param response_json: Data returned by control software.
        :type response_json: dict
        :return: Returns True if check passed, False otherwise
        :rtype: bool
        """
        try:
            if response_json['status'] == 'ERROR':
                if response_json['code'] == -1:
                    raise CommunicationError(endpoint=response_json['endpoint'],
                                             description=response_json['description'])
                else:
                    raise DeviceError(name=response_json['name'], code=response_json['code'],
                                      description=response_json['description'])

            else:
                return True

        except (CommunicationError, DeviceError) as ex:
            bfc_logger.error(str(ex))
            return False

    @staticmethod
    def __handle_value_response(response: dict):
        """
        Tries to extract the value of a response JSON and handles possible errors during operation.

        :param response: JSON response of the control software.
        :type response: dict
        :return: Value extracted from the response. Returns 0 if errors were raised.
        """
        try:
            bfc_logger.debug(f"Reading content from {response['name']}.")
            if response['type'] is not None:
                value_dict = response['content']['latest_valid_value']
                if value_dict['outdated'] or value_dict['status'] != 'SYNCHRONIZED':
                    raise ValueNotSynchronizedWarning(value_name=response['name'], date=value_dict['date'],
                                                      outdated=value_dict['outdated'], status=value_dict['status'])

                else:
                    return value_dict['value']

            else:
                raise EmptyValueError(value_name=response['name'])

        except (KeyError, EmptyValueError) as ex:
            bfc_logger.error(f"Failed to handle response json. {str(ex)}")
            return 0

        except ValueNotSynchronizedWarning as ex:
            bfc_logger.warning(str(ex))
            return value_dict['value']

    # GENERAL SYSTEM FUNCTIONS
    def system_info(self):
        self.__check_permission(required_permission=UNAUTHENTICATED_MODE.permission)
        response = self.__generic_request(path=self.__make_endpoint('system'))
        if self.__json_check(response):
            bfc_logger.info(
                f"{response['system_name']} @{self.__protocol}{self.ip}:{self.port}\n"
                f"System version {response['system_version']}\n"
                f"API version {response['api_version']}")

            return response['system_name'], response['system_version'], response['api_version']

        else:
            return '', '', ''

    # TEMPERATURE CONTROL
    def set_pid_parameters(self, p: float, i: float, d: float):
        self.__check_permission(required_permission=OPERATOR_MODE.permission)
        pass
