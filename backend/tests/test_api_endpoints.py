"""
API端点测试

测试FastAPI应用的所有API端点，包括请求验证、响应格式、错误处理等
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from .test_app_factory import create_test_app


# ==================== /api/query 端点测试 ====================

@pytest.mark.api
class TestQueryEndpoint:
    """测试 /api/query 端点"""

    def test_query_success_with_session_id(self, test_client, sample_query_request, sample_query_response):
        """测试带session_id的成功查询"""
        response = test_client.post("/api/query", json=sample_query_request)

        assert response.status_code == 200
        data = response.json()

        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["session_id"] == sample_query_request["session_id"]
        assert isinstance(data["sources"], list)

    def test_query_success_without_session_id(self, test_client):
        """测试不带session_id的成功查询（应自动创建）"""
        request_data = {"query": "What courses are available?"}
        response = test_client.post("/api/query", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["session_id"] is not None  # 应该自动创建

    def test_query_with_empty_query(self, test_client):
        """测试空查询字符串"""
        request_data = {"query": ""}
        response = test_client.post("/api/query", json=request_data)

        # 应该返回成功，但可能返回空答案或提示
        assert response.status_code in [200, 400, 422]

    def test_query_missing_query_field(self, test_client):
        """测试缺少query字段"""
        request_data = {"session_id": "test-123"}
        response = test_client.post("/api/query", json=request_data)

        # Pydantic验证应该失败
        assert response.status_code == 422

    def test_query_invalid_json(self, test_client):
        """测试无效的JSON格式"""
        response = test_client.post(
            "/api/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_query_with_long_query(self, test_client):
        """测试超长查询字符串"""
        long_query = "What is " + "very " * 1000 + "long question?"
        request_data = {"query": long_query}
        response = test_client.post("/api/query", json=request_data)

        # 应该能处理长查询
        assert response.status_code in [200, 400, 413]

    def test_query_response_structure(self, test_client, sample_query_request):
        """测试响应结构的完整性"""
        response = test_client.post("/api/query", json=sample_query_request)

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert isinstance(data["session_id"], str)

        # 验证sources结构
        if len(data["sources"]) > 0:
            source = data["sources"][0]
            assert "title" in source
            assert "link" in source

    def test_query_rag_system_error(self, mock_rag_system):
        """测试RAG系统抛出异常时的处理"""
        # 配置mock抛出异常
        mock_rag_system.query.side_effect = Exception("RAG system error")

        app = create_test_app(mock_rag_system)
        client = TestClient(app)

        request_data = {"query": "test query"}
        response = client.post("/api/query", json=request_data)

        assert response.status_code == 500
        assert "detail" in response.json()


# ==================== /api/courses 端点测试 ====================

@pytest.mark.api
class TestCoursesEndpoint:
    """测试 /api/courses 端点"""

    def test_get_courses_success(self, test_client, sample_course_stats):
        """测试成功获取课程统计"""
        response = test_client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        assert "total_courses" in data
        assert "course_titles" in data
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)

    def test_get_courses_empty_catalog(self, mock_rag_system):
        """测试空课程目录"""
        # 配置返回空数据
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": []
        }

        app = create_test_app(mock_rag_system)
        client = TestClient(app)

        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 0
        assert len(data["course_titles"]) == 0

    def test_get_courses_multiple_courses(self, mock_rag_system, sample_course_stats):
        """测试多个课程的情况"""
        mock_rag_system.get_course_analytics.return_value = sample_course_stats

        app = create_test_app(mock_rag_system)
        client = TestClient(app)

        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == sample_course_stats["total_courses"]
        assert len(data["course_titles"]) == sample_course_stats["total_courses"]

    def test_get_courses_rag_system_error(self, mock_rag_system):
        """测试RAG系统错误时的处理"""
        mock_rag_system.get_course_analytics.side_effect = Exception("Database error")

        app = create_test_app(mock_rag_system)
        client = TestClient(app)

        response = client.get("/api/courses")

        assert response.status_code == 500
        assert "detail" in response.json()


# ==================== /api/clear-session 端点测试 ====================

@pytest.mark.api
class TestClearSessionEndpoint:
    """测试 /api/clear-session 端点"""

    def test_clear_session_success(self, test_client):
        """测试成功清除会话"""
        request_data = {"session_id": "test-session-123"}
        response = test_client.post("/api/clear-session", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_clear_session_missing_session_id(self, test_client):
        """测试缺少session_id字段"""
        request_data = {}
        response = test_client.post("/api/clear-session", json=request_data)

        # Pydantic验证应该失败
        assert response.status_code == 422

    def test_clear_session_invalid_session_id(self, test_client):
        """测试无效的session_id"""
        request_data = {"session_id": ""}
        response = test_client.post("/api/clear-session", json=request_data)

        # 应该接受空字符串（由session_manager处理）
        assert response.status_code in [200, 400]

    def test_clear_session_error(self, mock_rag_system):
        """测试清除会话时的错误处理"""
        mock_rag_system.session_manager.clear_session.side_effect = Exception("Session error")

        app = create_test_app(mock_rag_system)
        client = TestClient(app)

        request_data = {"session_id": "test-session"}
        response = client.post("/api/clear-session", json=request_data)

        assert response.status_code == 500
        assert "detail" in response.json()


# ==================== 根端点和健康检查测试 ====================

@pytest.mark.api
class TestMiscEndpoints:
    """测试其他端点"""

    def test_root_endpoint(self, test_client):
        """测试根端点"""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_health_check(self, test_client):
        """测试健康检查端点"""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_invalid_endpoint(self, test_client):
        """测试不存在的端点"""
        response = test_client.get("/api/nonexistent")

        assert response.status_code == 404

    def test_method_not_allowed(self, test_client):
        """测试不允许的HTTP方法"""
        # /api/courses 只允许GET
        response = test_client.post("/api/courses", json={})

        assert response.status_code == 405


# ==================== CORS和中间件测试 ====================

@pytest.mark.api
class TestMiddleware:
    """测试中间件功能"""

    def test_cors_headers(self, test_client):
        """测试CORS头部"""
        response = test_client.options(
            "/api/query",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )

        # 验证CORS响应头
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_cors_preflight(self, test_client):
        """测试CORS预检请求"""
        response = test_client.options("/api/courses")

        assert response.status_code == 200


# ==================== 集成测试 ====================

@pytest.mark.integration
class TestAPIIntegration:
    """API集成测试"""

    def test_query_and_get_courses_workflow(self, test_client):
        """测试完整的查询工作流"""
        # 1. 获取课程列表
        courses_response = test_client.get("/api/courses")
        assert courses_response.status_code == 200

        # 2. 进行查询
        query_response = test_client.post(
            "/api/query",
            json={"query": "What courses are available?"}
        )
        assert query_response.status_code == 200

        session_id = query_response.json()["session_id"]

        # 3. 使用相同session_id进行后续查询
        followup_response = test_client.post(
            "/api/query",
            json={
                "query": "Tell me more about the first course",
                "session_id": session_id
            }
        )
        assert followup_response.status_code == 200
        assert followup_response.json()["session_id"] == session_id

        # 4. 清除会话
        clear_response = test_client.post(
            "/api/clear-session",
            json={"session_id": session_id}
        )
        assert clear_response.status_code == 200

    def test_multiple_concurrent_sessions(self, test_client):
        """测试多个并发会话"""
        # 创建多个会话
        session_ids = []
        for i in range(3):
            response = test_client.post(
                "/api/query",
                json={"query": f"Query {i}"}
            )
            assert response.status_code == 200
            session_ids.append(response.json()["session_id"])

        # 验证session_id都不同
        assert len(set(session_ids)) == 3

        # 清除所有会话
        for session_id in session_ids:
            response = test_client.post(
                "/api/clear-session",
                json={"session_id": session_id}
            )
            assert response.status_code == 200


# ==================== 性能和边界测试 ====================

@pytest.mark.api
class TestPerformanceAndBoundaries:
    """性能和边界条件测试"""

    def test_large_response_handling(self, mock_rag_system):
        """测试处理大型响应"""
        # 配置返回大量数据
        large_answer = "This is a very long answer. " * 1000
        large_sources = [
            {"title": f"Source {i}", "link": f"https://example.com/{i}"}
            for i in range(50)
        ]

        mock_rag_system.query.return_value = (large_answer, large_sources)

        app = create_test_app(mock_rag_system)
        client = TestClient(app)

        response = client.post("/api/query", json={"query": "test"})

        assert response.status_code == 200
        data = response.json()
        assert len(data["answer"]) > 0
        assert len(data["sources"]) == 50

    def test_special_characters_in_query(self, test_client):
        """测试查询中的特殊字符"""
        special_queries = [
            "What is <script>alert('xss')</script>?",
            "Query with émojis 🚀 and ünïcödé",
            "SQL injection'; DROP TABLE courses;--",
            "Path traversal ../../etc/passwd"
        ]

        for query in special_queries:
            response = test_client.post(
                "/api/query",
                json={"query": query}
            )
            # 应该安全处理，不崩溃
            assert response.status_code in [200, 400, 422]

    def test_concurrent_requests(self, test_client):
        """测试并发请求处理"""
        import concurrent.futures

        def make_request():
            return test_client.post(
                "/api/query",
                json={"query": "test query"}
            )

        # 发送10个并发请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [f.result() for f in futures]

        # 所有请求都应该成功
        for response in responses:
            assert response.status_code == 200
