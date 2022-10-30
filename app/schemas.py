from typing import Union, Optional

from pydantic import BaseModel, IPvAnyAddress, EmailStr

class Ip(BaseModel):
    id: int
    owner_id: Optional[int]
    value: Optional[IPvAnyAddress] = None
    description: Union[str, None] = None
    class Config:
        orm_mode = True

class IpCreate(Ip):
    pass

class User(BaseModel):
    is_active: Optional[bool] = True
    ips: list[Ip] = []
    email: EmailStr
    is_admin: Optional[bool] = False
    class Config:
        orm_mode = True

class UserCreate(User):
    password: str

class TokenData(BaseModel):
    username: Optional[str] = None