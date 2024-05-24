import pydantic.class_validators as py_validators
from pydantic import BaseModel, EmailStr, model_validator


# Shared properties
class UserBase(BaseModel):
    is_active: bool | None = True
    is_superuser: bool = False
    username: str | None = None
    email: EmailStr | None = None
    full_name: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    scope: str | None = None

    @py_validators.validator("username")
    def username_check(cls, v, values):
        if not v.isalnum:
            raise ValueError("username must be alphanumeric")
        return v


# Properties to receive via API on creation
class UserCreate(UserBase):
    username: str
    password: str
    scope: str | None = None

    @model_validator(mode = "after")
    def username_validator(self):
        if not self.scope:
            self.scope = "me"
        return self


class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    # scope: str | None = None
    email: EmailStr | None = None


class UserInDBBase(UserBase):
    id: int | None = None

    class Config:
        # orm_mode = True
        from_attributes = True


# Additional properties to return via API
class UserOut(UserInDBBase):
    pass


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str
    scope: str
