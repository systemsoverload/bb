from dataclasses import dataclass
from typing import Generic, NoReturn, TypeVar, Union

OkType = TypeVar("OkType")
ErrType = TypeVar("ErrType", bound=Exception)


@dataclass
class User:
    display_name: str
    uuid: str


class Ok(Generic[OkType]):
    def __init__(self, value: OkType) -> None:
        self._value = value

    def unwrap(self) -> OkType:
        return self._value

    def unwrap_err(self) -> NoReturn:
        """Raises an exception since Ok variant contains no error"""
        raise ValueError("Called unwrap_err on Ok variant")

    def is_ok(self) -> bool:
        """Check if this is an Ok variant"""
        return True

    def is_err(self) -> bool:
        """Check if this is an Err variant"""
        return False


class Err(Generic[ErrType]):
    def __init__(self, exception: ErrType) -> None:
        self._exception = exception

    def unwrap(self) -> NoReturn:
        raise self._exception

    def unwrap_err(self) -> ErrType:
        """Return the error/exception contained in this Err variant"""
        return self._exception

    def is_ok(self) -> bool:
        """Check if this is an Ok variant"""
        return False

    def is_err(self) -> bool:
        """Check if this is an Err variant"""
        return True


# Define Result as a generic type alias
Result = Union[Ok[OkType], Err[ErrType]]
