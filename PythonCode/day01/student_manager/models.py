from pydantic import BaseModel, Field,EmailStr,ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"

class StudentStatus(str, Enum):
    active = "active"#在读
    graduated = "graduated"#毕业
    suspended = "suspended"#休学
    withdrawn = "withdrawn"#退学

class StudentBase(BaseModel):
    #学生基础模型
    name:str = Field(...,min_length=2,max_length=50,description="学生姓名")
    gender:Gender
    age:int = Field(ge=5,le=100,description="学生年龄")
    phone:str = Field(...,pattern="^1[3-9]\\d{9}$",description="学生手机号")
    email:Optional[EmailStr] = None
    address:Optional[str] = Field(None,max_length=200,description="学生地址")

class StudentCreate(StudentBase):
    #创建学生时的请求模型
    parent_name:str = Field(...,min_length=2,max_length=50)
    parent_phone:str = Field(...,pattern="^1[3-9]\\d{9}$")

class StudentUpdate(StudentBase):
    #更新学生时的请求模型全部字段可选
    name:Optional[str] = Field(None,min_length=2,max_length=50)
    gender:Optional[Gender] = None
    age:Optional[int] = Field(None,ge=5,le=100)
    phone:Optional[str] = Field(None,pattern="^1[3-9]\\d{9}$")
    email:Optional[EmailStr] = None
    address:Optional[str] = Field(None,max_length=200)
    status:Optional[StudentStatus] = None
class Student(StudentBase):
    #学生模型 响应模型
    id:int
    student_no:str #学号
    status:StudentStatus
    created_at:datetime
    updated_at:datetime
    model_config = ConfigDict(
        use_enum_values=True
    )
class StudentListResponse(BaseModel):
    total:int
    page:int
    page_size:int
    students:list[Student]




