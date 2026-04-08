from fastapi import APIRouter, HTTPException,Query
from typing import Optional
from datetime import datetime   
from models import (Course, Enrollment, EnrollmentCreate, EnrollmentStatus)
from database import courses_db

router = APIRouter(prefix="/api/v1/courses",tags=["课程管理"])

@router.get("",summary="获取课程列表")
def list_courses(
    page:int = Query(1,ge=1,description="页码"),
    page_size:int = Query(10,ge=1,le=100,description="每页数量")
    ):
    """
    获取课程列表
    返回所有课程，支持分页
    """
    courses = list(courses_db.values())
    start = (page-1)*page_size
    end = start+page_size
    page_courses_dict = courses[start:end]
    print(page_courses_dict)
    page_courses = [Course(**c) for c in page_courses_dict]
    total = len(courses)
    return {"total":total,"page":page,"page_size":page_size,"courses":page_courses}
    
   

