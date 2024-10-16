from pydantic import BaseModel


class NewMessage(BaseModel):
    text: str
