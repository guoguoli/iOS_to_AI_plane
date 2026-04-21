"""成都教育科技 - AI题库服务"""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="AI题库服务", version="1.0.0")

class Question(BaseModel):
    """题目模型"""
    content: str
    subject: str
    difficulty: int  # 1-5

@app.get("/")
async def root():
    return {"message": "成都教育科技AI题库服务", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/questions/")
async def create_question(question: Question):
    return {"id": "Q001", **question.model_dump()}

@app.get("/questions/{question_id}")
async def get_question(question_id: str):
    return {
        "id": question_id,
        "content": "请用一句话描述春天的特点",
        "subject": "语文",
        "difficulty": 2
    }
