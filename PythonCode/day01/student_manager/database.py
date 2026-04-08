from typing import Dict
from datetime import datetime
# 模拟数据库
students_db: Dict[int, dict] = {
    1: {
        "id": 1,
        "student_no": "CD2024001",
        "name": "张小明",
        "gender": "male",
        "age": 12,
        "phone": "13812345678",
        "email": "zhangxm@email.com",
        "address": "成都市武侯区",
        "parent_name": "张先生",
        "parent_phone": "13912345678",
        "status": "active",
        "created_at": datetime(2024, 1, 15, 9, 0),
        "updated_at": datetime(2024, 1, 15, 9, 0)
    },
    2: {
        "id": 2,
        "student_no": "CD2024002",
        "name": "李小红",
        "gender": "female",
        "age": 10,
        "phone": "13723456789",
        "email": None,
        "address": "成都市锦江区",
        "parent_name": "李女士",
        "parent_phone": "13823456789",
        "status": "active",
        "created_at": datetime(2024, 2, 1, 10, 30),
        "updated_at": datetime(2024, 2, 1, 10, 30)
    }
}
def get_next_id() -> int:
    return max(students_db.keys(),default=0)+1
def generate_student_no() -> str:
    year = datetime.now().year
    count = len(students_db)+1
    return f"CD{year}{count:04d}"
courses_db: Dict[int, dict] = {
    # 1: Course(id=1, name="Python基础", teacher="张老师", capacity=30, enrolled=15),
    # 2: Course(id=2, name="FastAPI实战", teacher="李老师", capacity=20, enrolled=10),
    # 3: Course(id=3, name="AI应用开发", teacher="王老师", capacity=25, enrolled=8),
    1: {
        "id":1,
        "name":"Python基础",
        "teacher":"张老师",
        "capacity":30,
        "enrolled":0
    },
    2: {
        "id":2,
        "name":"FastAPI实战",
        "teacher":"李老师",
        "capacity":20,
        "enrolled":0
    },
    3: {
        "id":3,
        "name":"AI应用开发",
        "teacher":"王老师",
        "capacity":25,
        "enrolled":0
    }
}
