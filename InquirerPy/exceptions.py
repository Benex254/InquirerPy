"""Module contains exceptions dedicated to InquirerPy."""


from typing import Optional


class InvalidArgument(Exception):
    """Invalid parameter type."""

    def __init__(self, message: Optional[str]):
        """Construct the exception.

        :param message: the exception message
        :type message: str
        """
        self.message = "Invalid argument type" if not message else message
        super().__init__(self.message)


class RequiredKeyNotFound(Exception):
    """Required keys for question is not present."""

    def __init__(self, message="Required keys for question is not present"):
        """Construct the exception.

        :param message: the exception message
        :type message: str
        """
        self.message = message
        super().__init__(self.message)
