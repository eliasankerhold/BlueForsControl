from datetime import datetime


class InsufficientPermissionError(Exception):
    """
    Raised if the caller of a function does not have the required permission.
    """

    def __init__(self, required_permission: int, actual_permission: int):
        """
        Initializes InsufficientPermissionError.

        :param required_permission: Permission required for function execution.
        :type required_permission: int
        :param actual_permission: Permission of the caller.
        :type actual_permission: int
        """

        self.message = (f"Operation requires permission level {required_permission}, "
                        f"but was called from permission level {actual_permission}.")

        super().__init__(self.message)


class DeviceError(Exception):
    """
    Raised if an erroneous response is received from the control software.
    """

    def __init__(self, name: str, code: int, description: str):
        """
        Initializes DeviceError.

        :param name: Name of the error as returned by BlueFors control software.
        :type name: str
        :param code: Error code according to BlueFors control software.
        :type code: int
        :param description: Human-readable description of the error.
        :type description: str
        """
        self.message = f"{name} (CODE {code}): {description}"
        super().__init__(self.message)


class CommunicationError(Exception):
    """
    Raised if there is faulty or failed communication between control software and script.
    """

    def __init__(self, endpoint: str, description: str, content: dict = None):
        """
        Initializes CommunicationError.

        :param endpoint: Endpoint with which communication was attempted, including query parameters. API key will be
            protected.
        :type endpoint: str
        :param content: If POST request, the content that was attached.
        :type content: dict
        """
        if 'key' in endpoint:
            pass

        if content is None:
            self.message = f"Faulty communication with endpoint {endpoint}. {description}"
        else:
            self.message = f"Faulty communication of data {content} with endpoint {endpoint}. {description}"

        super().__init__(self.message)


class EmptyValueError(Exception):
    """
    Raised if trying to access data from a value that is empty in the control software.
    """

    def __init__(self, value_name: str):
        """
        Initializes EmptyValueError.

        :param value_name: Name of the value that failed to be accessed.
        :type value_name: str
        """
        self.message = f"Failed to access {value_name}. This value has no content."
        super().__init__(self.message)


class ValueStatusWarning(Exception):
    """
    Raised if the status of a value returned by the control software is not 'SYNCHRONIZED', 'INDEPENDENT'
    or the value is flagged as 'outdated'.
    """

    def __init__(self, value_name: str, date: int, outdated: bool, status: str):
        """
        Initializes ValueStatusWarning.

        :param value_name: Name of the value that failed to be accessed.
        :type value_name: str
        """
        out = 'outdated' if outdated else 'not outdated'

        self.message = f"Value {value_name} is {out} and {status}. Timestamp: {datetime.fromtimestamp(date)}"
        super().__init__(self.message)
