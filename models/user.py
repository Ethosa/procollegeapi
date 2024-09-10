from pydantic import BaseModel


class LoginUser(BaseModel):
    login: str
    password: str


class Signed(BaseModel):
    access_token: str
