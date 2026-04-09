from fastapi import FastAPI
from routers.students import router as students_router
from routers.course import router as course_router

app = FastAPI(
    title="学生管理系统",
    description="学生信息管理API",
    version="1.0.0"
)
app.include_router(students_router)
app.include_router(course_router)

@app.get("/")
def root():
    return {
        "message":"成都教育科技学生管理系统",
        "version":"1.0.1",
        "docs":"/docs"
    }
@app.get("/health")
def health():
    return {"status":"healthy"}
if __name__ == "__main__":
    import uvicorn
    # from pyngrok import ngrok
    # public_url = ngrok.connect(8000)
    # print("✅ 外网访问地址：", public_url)
    uvicorn.run(app,host="0.0.0.0",port=8000)