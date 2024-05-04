from typing import AsyncIterator, Callable, Self, Sequence


class PaginationHelper[T](AsyncIterator[Sequence[T]]):
    def __init__(
        self,
        request: Callable[[], AsyncIterator[T]],
        *,
        item_count: int,
        page_size: int = 20,
    ):
        self._request = request
        self._page_size = page_size
        self._item_count = item_count
        self._state: AsyncIterator[T] | None = None

    @property
    def page_count(self) -> int:
        return (self._item_count + self._page_size - 1) // self._page_size

    def __aiter__(self) -> Self:
        self._state = self._request()
        return self

    async def __anext__(self) -> Sequence[T]:
        if self._state is None:
            raise RuntimeError(f"{self.__class__.__name__} must be used inside async for loop")
        items: list[T] = []
        try:
            for _ in range(self._page_size):
                items.append(await self._state.__anext__())
        except StopAsyncIteration:
            if not items:
                raise StopAsyncIteration() from None
        return items
