from fastapi import APIRouter, HTTPException,Query
from typing import Optional
from datetime import datetime
from models import (Student, StudentCreate, StudentUpdate, StudentListResponse,StudentStatus)
from database import students_db, get_next_id, generate_student_no
router = APIRouter(prefix="/api/v1/students",tags=["学生管理"])
@router.get("",response_model=StudentListResponse)
def list_students(
    page:int=Query(1,ge=1,description="页码"),
    page_size:int=Query(10,ge=1,le=100,description="每页数量"),
    search:Optional[str]=Query(None,description="搜索关键词(姓名/手机号)"),
    status:Optional[StudentStatus]=Query(None,description="学生状态")
):
    """
    获取学生列表
    支持：
    -分页查询
    -搜索关键词（手机号/姓名）
    -学生状态过滤
    """ 
    students = list(students_db.values())
    if search:
        search = search.lower()
        students = [
            s for s in students
            if search in s["name"].lower() or search in s["phone"].lower()
        ]
    if status:
        students = [s for s in students if s["status"] == status.value]
    students.sort(key=lambda x:x["created_at"],reverse=True)

    total = len(students)
    start = (page-1)*page_size
    end = start+page_size
    page_students = students[start:end]
    return StudentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        students=[Student(**s) for s in page_students]
    )
@router.get("/{student_id}",response_model=Student)
def get_student(student_id:int):
    #获取学生详情
    if student_id not in students_db:
        raise HTTPException(status_code=404,detail="学生不存在")
    return Student(**students_db[student_id])
@router.post("",response_model=Student,status_code=201)
def create_student(student:StudentCreate):
    #创建学生
    for s in students_db.values():
        if s["phone"] == student.phone:
            raise HTTPException(status_code=400,detail="手机号已被注册")
    now = datetime.now()
    new_student = {
        "id": get_next_id(),
        "student_no": generate_student_no(),
        **student.model_dump(),
        "created_at": now,
        "status":"active",
        "updated_at": now
    }
    students_db[new_student["id"]] = new_student
    return Student(**new_student)
@router.put("/{student_id}",response_model=Student)
def update_student(student_id:int,student:StudentUpdate):
    #更新学生信息
    if student_id not in students_db:
        raise HTTPException(status_code=404,detail="学生不存在")
    existing = students_db[student_id]
    update_data = student.model_dump(exclude_unset=True)
    for field,value in update_data.items():
        existing[field] = value
    existing["updated_at"] = datetime.now()
    students_db[student_id] = existing
    return Student(**existing)
@router.delete("/{student_id}",status_code=204)
def delete_student(student_id:int):
    #删除学生
    if student_id not in students_db:
        raise HTTPException(status_code=404,detail="学生不存在")
    students_db[student_id]["status"] = "withdrawn"
    students_db[student_id]["updated_at"] = datetime.now()
