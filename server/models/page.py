from pydantic import BaseModel


class PaginatedResponse[T](BaseModel):
    page: int
    total_pages: int
    result: list[T]
