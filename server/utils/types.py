type JsonPrimitive = str | int | bool | float | None
type JsonT = dict[str, JsonT] | list[JsonT] | JsonPrimitive
