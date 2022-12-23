from typing import Union, Optional

from pydantic import BaseModel, IPvAnyAddress, EmailStr, AnyUrl

class InstantAccess(BaseModel):
    id: Optional[int]
    owner_id: Optional[int]
    link: AnyUrl
    unique_link: str = None
    description: Union[str, None] = None
    class Config:
        orm_mode = True

class InstantAccessCreate(InstantAccess):
    pass

class Ip(BaseModel):
    id: Optional[int]
    owner_id: Optional[int]
    value: IPvAnyAddress
    description: Union[str, None] = None
    origin: str = None
    class Config:
        orm_mode = True

class IpCreate(Ip):
    pass
    

class User(BaseModel):
    is_active: Optional[bool] = True
    ips: list[Ip] = []
    email: EmailStr
    is_admin: Optional[bool] = False
    twofactor: str = None
    class Config:
        orm_mode = True

class UserCreate(User):
    password: str

class TokenData(BaseModel):
    username: Optional[str] = None

class Token(BaseModel):
    id: Optional[int]
    owner_id: Optional[int]
    key: str = None
    secret: str = None
    description: Union[str, None] = None
    class Config:
        orm_mode = True

class TokenCreate(Token):
    pass