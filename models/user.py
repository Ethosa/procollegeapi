from pydantic import BaseModel


class LoginUser(BaseModel):
    """
    Модель для авторизации пользователя
    """
    login: str
    password: str


class EditUser(BaseModel):
    """
    Модель для обновления информации о пользователе
    """
    description: str | None = None
    city: str | None = None
    interests: list[str] | None = None
