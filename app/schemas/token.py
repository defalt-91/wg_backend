from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str
    # scopes: str | None


class TokenData(BaseModel):
    sub: str | None = None
    scopes: list[str] = []


class Message(BaseModel):
    message: str


class NewPassword(BaseModel):
    token: str
    new_password: str
