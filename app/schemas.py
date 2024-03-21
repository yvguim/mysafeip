from typing import Union, Optional

from pydantic import ConfigDict, BaseModel, IPvAnyAddress, EmailStr, AnyUrl

class InstantAccess(BaseModel):
    id: Optional[int] = None
    owner_id: Optional[int] = None
    link: AnyUrl
    unique_link: str = None
    description: Union[str, None] = None
    model_config = ConfigDict(from_attributes=True)

class InstantAccessCreate(InstantAccess):
    pass

class Ip(BaseModel):
    id: Optional[int] = None
    owner_id: Optional[int] = None
    value: IPvAnyAddress
    description: Union[str, None] = None
    origin: str = None
    model_config = ConfigDict(from_attributes=True)

class IpCreate(Ip):
    pass
    

class User(BaseModel):
    is_active: Optional[bool] = True
    ips: list[Ip] = []
    email: EmailStr
    is_admin: Optional[bool] = False
    twofactor: str = None
    model_config = ConfigDict(from_attributes=True)

class UserCreate(User):
    password: str

class TokenData(BaseModel):
    username: Optional[str] = None

class Token(BaseModel):
    id: Optional[int] = None
    owner_id: Optional[int] = None
    key: str = None
    secret: str = None
    description: Union[str, None] = None
    model_config = ConfigDict(from_attributes=True)

class TokenCreate(Token):
    pass
