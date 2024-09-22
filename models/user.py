from pydantic import BaseModel


class LoginUser(BaseModel):
    login: str
    password: str


class EditUser(BaseModel):
    description: str | None = None
    city: str | None = None
    interests: list[str] | None = None

class Signed(BaseModel):
    access_token: str
