from typing import Optional

from pydantic import BaseModel
import pydantic.class_validators as py_validators


# Shared properties
class UserBase(BaseModel):
    is_active: Optional[bool] = True
    is_superuser: bool = False
    username: Optional[str] = None
    @py_validators.validator("username")
    def username_check(cls, v, values):
        if not v.isalnum:
            raise ValueError("username must be alphanumeric")
        return v

# Properties to receive via API on creation
class UserCreate(UserBase):
    username: str
    password: str


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDBBase(UserBase):
    id: Optional[int] = None

    class Config:
        # orm_mode = True
        from_attributes= True


# Additional properties to return via API
class User(UserInDBBase):
    pass


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str
