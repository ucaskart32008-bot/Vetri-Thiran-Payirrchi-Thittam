from pydantic import BaseModel,EmailStr,Field,ConfigDict
class RegisterIn(BaseModel):
    name:str=Field(min_length=2,max_length=100)
    email:EmailStr
    password:str=Field(min_length=8,max_length=128)
class UserOut(BaseModel):
    id:int
    name:str
    email:EmailStr
    model_config=ConfigDict(from_attributes=True)
class HomeIn(BaseModel):
    budget:int=Field(gt=0,le=100000000)
    rooms:list[str]=Field(min_length=1,max_length=8)
    style:str=Field(default="Modern",max_length=80)
    household_size:int=Field(default=2,ge=1,le=50)
    priorities:str=Field(default="",max_length=500)
class PartyIn(BaseModel):
    budget:int=Field(gt=0,le=100000000)
    guests:int=Field(ge=1,le=10000)
    event_type:str=Field(min_length=2,max_length=100)
    venue:str=Field(default="Flexible",max_length=200)
    preferences:str=Field(default="",max_length=500)
