class AlreadyExistsError(ValueError):
    def __init__(self, entity: str, field: str, value: str) -> None:
        self._entity = entity
        self._field = field
        self.value = value
        super().__init__(f'{entity} with {field} "{value}" already exists')


class UserAlreadyExistsError(AlreadyExistsError):
    def __init__(self, username: str) -> None:
        super().__init__("User", "username", username)


class PlayerAlreadyExistsError(AlreadyExistsError):
    def __init__(self, nickname: str) -> None:
        super().__init__("Player", "nickname", nickname)


class NotFoundError(ValueError):
    def __init__(self, entity: str, field: str, value: str) -> None:
        self._entity = entity
        self._field = field
        self.value = value
        super().__init__(f'{entity} with {field} "{value}" not found')


class UserNotFoundError(NotFoundError):
    def __init__(self, username: str) -> None:
        super().__init__("User", "username", username)


class InvalidPasswordError(ValueError):
    def __init__(self) -> None:
        super().__init__("Invalid password")
