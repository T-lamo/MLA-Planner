from typing import Annotated

from pydantic import BaseModel, constr


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class PasswordChangeRequest(BaseModel):
    current_password: Annotated[str, constr(min_length=6)]
    new_password: Annotated[str, constr(min_length=6)]
