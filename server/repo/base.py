class BaseRepo[T]:
    def __init__(self, connection: T) -> None:
        self._conn = connection
