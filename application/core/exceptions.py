class AppException(Exception):
    """Base class for all custom application exceptions."""

    def __init__(self, status_code: int, message: str, error_code: str, error_message: str):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        self.error_message = error_message


class UserAlreadyExistsException(AppException):
    def __init__(self, error_message: str):
        super().__init__(status_code=409, message="User already exists", error_code="USER_ALREADY_EXISTS", error_message=error_message)


class InvalidCredentialsException(AppException):
    def __init__(self, error_message: str = "Invalid email or password"):
        super().__init__(status_code=401, message="Authentication failed", error_code="INVALID_CREDENTIALS", error_message=error_message)


class UserNotFoundException(AppException):
    def __init__(self, error_message: str = "User not found in the system"):
        super().__init__(status_code=404, message="User not found", error_code="USER_NOT_FOUND", error_message=error_message)


class BadRequestException(AppException):
    def __init__(self, message: str = "Bad Request", error_message: str = "Bad Request Received"):
        super().__init__(status_code=400, message=message, error_code="BAD_REQUEST", error_message=error_message)


class UnauthorizedUserException(AppException):
    def __init__(self, message: str = "Unauthenticated User", error_message: str = "User is not authenticated"):
        super().__init__(status_code=401, message=message, error_code="UNAUTHORIZED_USER", error_message=error_message)
