import os
from abc import abstractmethod, ABC

from flamingo.core.debug.error import ValidationError


class Validator(ABC):
    """
    A simple validation class that's meant to validate the shape of an object
    """

    @abstractmethod
    def validate(self, value: object):
        """
        :param value: the object to be validated
        :raises ValidationError: when the object is malformed.
        """
