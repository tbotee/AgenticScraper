from pydantic import BaseModel

class Filter(BaseModel):
    key: str
    value: str


