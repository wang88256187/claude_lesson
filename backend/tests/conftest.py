"""
Pytest配置和共享fixtures

提供测试所需的mock对象、测试数据和辅助函数
"""
import pytest
from unittest.mock import Mock, MagicMock
from typing import List, Dict, Any
import tempfile
import shutil
import os


# ==================== 测试数据 fixtures ====================

@pytest.fixture
def sample_course_data():
    """提供示例课程数据"""
    return {
        "title": "Model Context Protocol Course",
        "instructor": "John Doe",
        "link": "https://example.com/mcp-course",
        "lessons": [
            {
                "number": 0,
                "title": "Introduction to MCP",
                "link": "https://example.com/mcp-course/lesson-0",
                "content": "This is an introduction to Model Context Protocol. MCP enables communication between AI models."
            },
            {
                "number": 1,
                "title": "MCP Architecture",
                "link": "https://example.com/mcp-course/lesson-1",
                "content": "Learn about the architecture of MCP. It consists of servers, clients, and protocols."
            }
        ]
    }


@pytest.fixture
def sample_query_request():
    """提供示例查询请求"""
    return {
        "query": "What is MCP?",
        "session_id": "test-session-123"
    }


@pytest.fixture
def sample_query_response():
    """提供示例查询响应"""
    return {
        "answer": "MCP (Model Context Protocol) is a protocol that enables communication between AI models.",
        "sources": [
            {
                "title": "Model Context Protocol Course - Lesson 0",
                "link": "https://example.com/mcp-course/lesson-0"
            }
        ],
        "session_id": "test-session-123"
    }


@pytest.fixture
def sample_course_stats():
    """提供示例课程统计数据"""
    return {
        "total_courses": 2,
        "course_titles": [
            "Model Context Protocol Course",
            "Advanced RAG Systems"
        ]
    }


# ==================== Mock组件 fixtures ====================

@pytest.fixture
def mock_config():
    """创建mock配置对象"""
    config = Mock()
    config.ANTHROPIC_API_KEY = "test-api-key-12345"
    config.ANTHROPIC_MODEL = "gemini-2.5-flash"
    config.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    config.CHUNK_SIZE = 800
    config.CHUNK_OVERLAP = 100
    config.MAX_RESULTS = 5
    config.MAX_HISTORY = 2
    config.CHROMA_PATH = "./test_chroma_db"
    return config


@pytest.fixture
def mock_vector_store():
    """创建mock向量存储对象"""
    vector_store = Mock()
    vector_store.search_course_content.return_value = [
        {
            "content": "MCP enables communication between AI models.",
            "metadata": {
                "course_title": "Model Context Protocol Course",
                "lesson_number": 0,
                "lesson_link": "https://example.com/mcp-course/lesson-0"
            }
        }
    ]
    vector_store.get_course_count.return_value = 2
    vector_store.get_existing_course_titles.return_value = [
        "Model Context Protocol Course",
        "Advanced RAG Systems"
    ]
    vector_store.resolve_course_name.return_value = "Model Context Protocol Course"
    return vector_store


@pytest.fixture
def mock_ai_generator():
    """创建mock AI生成器对象"""
    ai_generator = Mock()
    ai_generator.generate_response.return_value = "MCP (Model Context Protocol) is a protocol that enables communication between AI models."
    return ai_generator


@pytest.fixture
def mock_document_processor():
    """创建mock文档处理器对象"""
    processor = Mock()

    # 创建mock Course对象 (使用Mock而不是真实导入)
    mock_course = Mock()
    mock_course.title = "Model Context Protocol Course"
    mock_course.instructor = "John Doe"
    mock_course.link = "https://example.com/mcp-course"
    mock_course.lessons = [
        Mock(
            number=0,
            title="Introduction to MCP",
            link="https://example.com/mcp-course/lesson-0"
        )
    ]

    processor.process_course_document.return_value = (mock_course, [])
    return processor


@pytest.fixture
def mock_session_manager():
    """创建mock会话管理器对象"""
    session_manager = Mock()
    session_manager.create_session.return_value = "test-session-123"
    session_manager.get_conversation_history.return_value = []
    session_manager.add_exchange.return_value = None
    session_manager.clear_session.return_value = None
    return session_manager


@pytest.fixture
def mock_tool_manager():
    """创建mock工具管理器对象"""
    tool_manager = Mock()
    tool_manager.get_tool_definitions.return_value = [
        {
            "name": "search_course_content",
            "description": "Search for course content",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                }
            }
        }
    ]
    tool_manager.get_last_sources.return_value = [
        {
            "title": "Model Context Protocol Course - Lesson 0",
            "link": "https://example.com/mcp-course/lesson-0"
        }
    ]
    tool_manager.reset_sources.return_value = None
    return tool_manager


@pytest.fixture
def mock_rag_system(
    mock_config,
    mock_vector_store,
    mock_ai_generator,
    mock_document_processor,
    mock_session_manager,
    mock_tool_manager
):
    """创建完整的mock RAG系统"""
    rag_system = Mock()
    rag_system.config = mock_config
    rag_system.vector_store = mock_vector_store
    rag_system.ai_generator = mock_ai_generator
    rag_system.document_processor = mock_document_processor
    rag_system.session_manager = mock_session_manager
    rag_system.tool_manager = mock_tool_manager

    # 配置query方法返回值
    rag_system.query.return_value = (
        "MCP (Model Context Protocol) is a protocol that enables communication between AI models.",
        [
            {
                "title": "Model Context Protocol Course - Lesson 0",
                "link": "https://example.com/mcp-course/lesson-0"
            }
        ]
    )

    # 配置get_course_analytics方法返回值
    rag_system.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": [
            "Model Context Protocol Course",
            "Advanced RAG Systems"
        ]
    }

    return rag_system


# ==================== 临时文件和目录 fixtures ====================

@pytest.fixture
def temp_dir():
    """创建临时目录用于测试"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    # 清理
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_docs_folder(temp_dir, sample_course_data):
    """创建包含示例文档的临时文件夹"""
    docs_path = os.path.join(temp_dir, "docs")
    os.makedirs(docs_path, exist_ok=True)

    # 创建示例课程文档
    doc_path = os.path.join(docs_path, "mcp_course.txt")
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(f"Course Title: {sample_course_data['title']}\n")
        f.write(f"Course Link: {sample_course_data['link']}\n")
        f.write(f"Course Instructor: {sample_course_data['instructor']}\n\n")

        for lesson in sample_course_data['lessons']:
            f.write(f"Lesson {lesson['number']}: {lesson['title']}\n")
            f.write(f"Lesson Link: {lesson['link']}\n")
            f.write(f"{lesson['content']}\n\n")

    yield docs_path


# ==================== pytest配置钩子 ====================

def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line(
        "markers", "integration: 标记集成测试(需要外部依赖)"
    )
    config.addinivalue_line(
        "markers", "unit: 标记单元测试(不需要外部依赖)"
    )
    config.addinivalue_line(
        "markers", "api: 标记API端点测试"
    )
