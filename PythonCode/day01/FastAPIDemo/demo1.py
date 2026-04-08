from fastapi import FastAPI
from pydantic import BaseModel,Field
from typing import List, Optional
from datetime import datetime
import uvicorn

# 1.创建应用实例 

app = FastAPI(
    title="成都教育科技API",
    description="教育科技场景的API服务",
    version="1.0.0"

)

# 2.定义数据模型 (Pydantic)
class Course(BaseModel):
    #课程模型 
    id: int
    name: str = Field(...,min_length=2,max_length=100)
    teacher: str
    duration_hours: int = Field(ge=1,le=200)
    price:float = Field(ge=0)
    is_active:bool = True

class CourseCreate(BaseModel):
    #创建课程时的请求模型
    name:str
    teacher:str
    duration_hours:int
    price:float

courses_db:List[Course] = [
    Course(id=1,name="Python入门",teacher="老王",duration_hours=100,price=1000.0),
    Course(id=2,name="Java入门",teacher="老张",duration_hours=120,price=1500.0),
]

# 3.定义路由
@app.get("/")
def roote():
    #首页
    return {
        "message": "欢迎使用成都教育科技API",
        "version": "1.0.0",
        "docs":"/docs"
    }

@app.get("/health")
def health_check():
    #健康检查
    return {"status": "healthy","timestamp":datetime.now().isoformat()}

@app.get("/courses",response_model=List[Course])
def list_courses():
    #获取课程列表
    return courses_db
@app.get("/courses/{course_id}",response_model=Course)
def get_course(course_id:int):
    #获取单个课程
    for course in courses_db:
        if course.id == course_id:
            return course
    return {"message":"课程不存在"}

@app.post("/courses",response_model=Course,status_code=201)
def create_course(course:CourseCreate):
    #创建课程
    new_id = max([c.id for c in courses_db])+1
    new_course = Course(id=new_id,**course.model_dump())
    courses_db.append(new_course)
    return new_course
@app.put("/courses/{course_id}",response_model=Course)
def update_course(course_id:int,course:CourseCreate):
    #更新课程
    for i,c in enumerate(courses_db):
        if c.id == course_id:
            courses_db[i] = Course(id=course_id,**course.model_dump()) 
            return courses_db[i]
    return {"error":"课程不存在"}
@app.delete("/courses/{course_id}",status_code=204)
def delete_course(course_id:int):
    for i,c in enumerate(courses_db):
        if c.id == course_id:
            courses_db.pop(i)
            return 
    return {"error":"课程不存在"}
if __name__ == "__main__":
    print("🚀 启动开发服务器...")
    print("http://127.0.0.1:8000/docs")
    uvicorn.run(app,host="127.0.0.1",port=8000)
