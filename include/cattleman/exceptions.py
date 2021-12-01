from typing import Union, Tuple, Optional


class CattlemanException(RuntimeError):

    def __init__(self, msg: str):
        super(RuntimeError, self).__init__(msg)


class ResourceNotFoundException(CattlemanException):

    def __init__(self, resource_id: str):
        msg = f"Resource with ID '{resource_id}' not found."
        super(ResourceNotFoundException, self).__init__(msg)


class DatabaseNotFoundException(CattlemanException):

    def __init__(self, name: str):
        msg = f"Database with name '{name}' not found."
        super(DatabaseNotFoundException, self).__init__(msg)


class TypeMismatchException(CattlemanException):

    def __init__(self, expected: Union[str, type, Tuple[type]], received: object,
                 field: Optional[str] = None):
        # sanitize expected
        if isinstance(expected, type):
            expected = expected.__name__
        if isinstance(expected, tuple):
            expected = '|'.join(map(lambda k: k.__name__, expected))
        if not isinstance(expected, str):
            expected = type(expected).__name__
        # sanitize received
        if isinstance(received, type):
            received = received.__name__
        received = type(received).__name__
        # extra info
        extra = ""
        if field is not None:
            extra = f" for field '{field}'"
        # ---
        msg = f"Expected type '{expected}'{extra}, " \
              f"an object of type '{received}' was received instead."
        super(TypeMismatchException, self).__init__(msg)


class MissingParameterException(CattlemanException):

    def __init__(self, klass: type, method: str, parameter: str):
        msg = f"The method {klass.__name__}.{method} expects parameter '{parameter}' which was " \
              f"not passed."
        super(MissingParameterException, self).__init__(msg)
