import os
from re import Pattern

from flamingo.core.debug.error import ValidationError
from flamingo.core.vars.var_validator import Validator


class TypeValidator(Validator):
    def __init__(self, _type):
        self._type = _type

    def validate(self, value):
        if not isinstance(value, self._type):
            raise ValidationError(f"Expected {self._type.__name__}, got {type(value).__name__}")


class IntValidator(Validator):
    def __init__(self, minimum: int | None = None, maximum: int | None = None):
        """
        A simple validator class that checks if the given input can become an integer, and
        then checks optional bounds

        :param minimum: optional lowest value number
        :param maximum: optional highest value number
        """
        self.minimum = minimum
        self.maximum = maximum

    def validate(self, value: object):
        if not isinstance(value, str):
            return False

        if value.isnumeric():
            val = int(value)

            if self.minimum and val < self.minimum:
                return False

            if self.maximum and val > self.maximum:
                return False

        return False

class ListValidator(Validator):
    def __init__(self, item_validator: Validator = None, min_length: int = None, max_length: int = None):
        """
        A simple meta validator class that allows for validation of simple lists like List<String> with embedded validation

        :param item_validator: what each item will be validated against
        :param min_length: an optional minimum length of the list
        :param max_length: an optional maximum length of the list
        """
        self.item_validator = item_validator
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value: list):
        if not isinstance(value, list):
            raise ValidationError(f"Expected list, got {type(value).__name__}")

        if self.item_validator:
            for i, item in enumerate(value):
                try:
                    self.item_validator.validate(item)
                except ValidationError as e:
                    raise ValidationError(f"List item {i} invalid: {e.message}")

        if self.min_length is not None and len(value) < self.min_length:
            raise ValidationError(f"Expected list to contain at least ({self.min_length}) elements, got {len(value)}")

        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError(f"Expected list to contain at most {self.max_length} elements, got {len(value)}")


class LiteralValidator(Validator):
    def __init__(self, exact_strings: tuple[str, ...]):
        """
        A simple validator mostly for syntax purposes, such as enforcing a syntax like `range 1 to 5`, or even
        an action list.

        :param exact_strings: the string literals like 'into' or 'plus'
        """
        self.exact = exact_strings

    def validate(self, value):
        if str(value) not in self.exact:
            raise ValidationError(f"Syntax Error: Expected one of '{"', '".join(self.exact)}', got '{value}'")


class PathValidator(Validator):
    def __init__(self, must_exist=False, must_be_dir=False, must_be_file=False, re_filter: Pattern =None):
        self.must_exist = must_exist
        self.must_be_dir = must_be_dir
        self.must_be_file = must_be_file
        self.re_filter = re_filter

    def validate(self, value):
        if not isinstance(value, str):
            raise ValidationError(f"Expected path string, got {type(value).__name__}")

        # Expand just for the check, but validate the raw string
        check_path = os.path.expanduser(value)

        if self.must_exist and not os.path.exists(check_path):
            raise ValidationError(f"Path does not exist: {value}")

        if self.must_be_dir and os.path.exists(check_path):
            if not os.path.isdir(check_path):
                raise ValidationError(f"Path is not a directory: {value}")

        if self.must_be_file and os.path.exists(check_path):
            if not os.path.isfile(check_path):
                raise ValidationError(f"Path is not a file: {value}")
            
        if self.re_filter and not self.re_filter.match(check_path):
            raise ValidationError("Path doesn't conform to pattern")