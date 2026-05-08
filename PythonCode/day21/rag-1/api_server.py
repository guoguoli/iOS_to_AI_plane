"""
FastAPI RAG服务
"""
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn

from config import config
from rag_pipeline import RAGPipeline, RetrievalResult
from vector_store import get_vector_store


# ============== API模型 ==============

class QuestionRequest(BaseModel):
    """问答请求"""
    question: str = Field(..., description="用户问题")
    use_rag: bool = Field(True, description="是否使用RAG")
    stream: bool = Field(False, description="是否流式输出")


class SourceInfo(BaseModel):
    """来源信息"""
    content: str
    source: str
    score: float


class AnswerResponse(BaseModel):
    """回答响应"""
    answer: str
    sources: List[SourceInfo]
    usage: dict
    latency: float


class DocumentIndexRequest(BaseModel):
    """文档索引请求"""
    directory: str = Field(..., description="文档目录路径")


class StatsResponse(BaseModel):
    """统计信息"""
    collection: str
    document_count: int
    persist_directory: str


# ============== 应用实例 ==============

# 全局RAG管道
rag_pipeline: Optional[RAGPipeline] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理（启动 & 关闭）"""
    global rag_pipeline

    if not config.validate():
        print("⚠️  配置验证失败，部分功能可能不可用")

    rag_pipeline = RAGPipeline(
        vector_store=get_vector_store(),
        top_k=config.TOP_K
    )
    print("✅ RAG管道初始化完成")

    yield  # 应用运行期间

    # 关闭时的清理工作（如有需要可在此添加）


app = FastAPI(
    title="智能教育问答系统 API",
    description="基于RAG的智能问答系统",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["健康检查"])
async def root():
    """健康检查"""
    return {"status": "ok", "service": "RAG Education QA"}


@app.get("/stats", response_model=StatsResponse, tags=["管理"])
async def get_stats():
    """获取系统统计信息"""
    vs = get_vector_store()
    stats = vs.get_stats()
    
    return StatsResponse(
        collection=stats["name"],
        document_count=stats["count"],
        persist_directory=stats["persist_directory"]
    )


@app.post("/index", tags=["管理"])
async def index_documents(request: DocumentIndexRequest):
    """索引文档"""
    try:
        count = rag_pipeline.load_and_index(request.directory)
        return {"status": "success", "indexed_chunks": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask", response_model=AnswerResponse, tags=["问答"])
async def ask_question(request: QuestionRequest):
    """问答接口（非流式）"""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")
    
    try:
        response = rag_pipeline.generate(
            query=request.question,
            use_rag=request.use_rag
        )
        
        sources = [
            SourceInfo(
                content=src.content[:200] + "..." if len(src.content) > 200 else src.content,
                source=src.source,
                score=src.score
            )
            for src in response.sources
        ]
        
        return AnswerResponse(
            answer=response.answer,
            sources=sources,
            usage=response.usage,
            latency=response.latency
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask/stream", tags=["问答"])
async def ask_stream(request: QuestionRequest):
    """流式问答接口"""
    from sse_starlette.sse import EventSourceResponse
    
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")
    
    async def event_generator():
        try:
            # 首先发送检索结果
            contexts = rag_pipeline.retrieve(request.question)
            if contexts:
                yield {
                    "event": "context",
                    "data": json.dumps({
                        "count": len(contexts),
                        "sources": [
                            {
                                "source": ctx.source,
                                "score": ctx.score
                            }
                            for ctx in contexts
                        ]
                    })
                }
            
            # 流式生成
            async for chunk in rag_pipeline.generate_stream(
                query=request.question,
                use_rag=request.use_rag
            ):
                yield {
                    "event": "content",
                    "data": chunk
                }
            
            # 结束信号
            yield {
                "event": "done",
                "data": ""
            }
        
        except Exception as e:
            yield {
                "event": "error",
                "data": str(e)
            }
    
    return EventSourceResponse(event_generator())


# ============== 启动服务 ==============

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host=config.HOST,
        port=config.PORT,
        reload=True
    )