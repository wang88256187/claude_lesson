"""
测试应用工厂

创建独立的FastAPI测试应用，避免导入主应用时的静态文件挂载问题
"""
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from unittest.mock import Mock, patch


# ==================== Pydantic模型 ====================

class SourceLink(BaseModel):
    """源链接模型"""
    title: str
    link: str


class QueryRequest(BaseModel):
    """查询请求模型"""
    query: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    """查询响应模型"""
    answer: str
    sources: List[SourceLink]
    session_id: str


class ClearSessionRequest(BaseModel):
    """清除会话请求模型"""
    session_id: str


class CourseStats(BaseModel):
    """课程统计模型"""
    total_courses: int
    course_titles: List[str]


# ==================== 测试应用工厂 ====================

def create_test_app(mock_rag_system=None):
    """
    创建用于测试的FastAPI应用

    Args:
        mock_rag_system: Mock的RAG系统实例

    Returns:
        FastAPI应用实例
    """
    app = FastAPI(title="Course Materials RAG System (Test)", root_path="")

    # 启用CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 如果没有提供mock_rag_system，创建一个默认的Mock
    if mock_rag_system is None:
        mock_rag_system = Mock()
        mock_rag_system.query.return_value = (
            "Test response",
            [{"title": "Test Source", "link": "https://example.com"}]
        )
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": []
        }
        mock_rag_system.session_manager.create_session.return_value = "test-session"
        mock_rag_system.session_manager.clear_session.return_value = None

    # ==================== API端点 ====================

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        """处理查询请求"""
        try:
            # 创建会话ID（如果未提供）
            session_id = request.session_id
            if not session_id:
                session_id = mock_rag_system.session_manager.create_session()

            # 使用RAG系统处理查询
            answer, sources = mock_rag_system.query(request.query, session_id)

            return QueryResponse(
                answer=answer,
                sources=sources,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        """获取课程统计信息"""
        try:
            analytics = mock_rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/clear-session")
    async def clear_session(request: ClearSessionRequest):
        """清除会话"""
        try:
            mock_rag_system.session_manager.clear_session(request.session_id)
            return {"status": "success"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/")
    async def root():
        """根端点"""
        return {"message": "Course Materials RAG System API"}

    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return {"status": "healthy"}

    return app


# ==================== pytest fixture ====================

@pytest.fixture
def test_app(mock_rag_system):
    """提供测试应用fixture"""
    return create_test_app(mock_rag_system)


@pytest.fixture
def test_client(test_app):
    """提供测试客户端fixture"""
    from fastapi.testclient import TestClient
    return TestClient(test_app)
