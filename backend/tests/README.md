# RAG系统测试框架

本目录包含RAG课程问答系统的完整测试套件，涵盖API端点测试、单元测试和集成测试。

## 📁 测试结构

```
backend/tests/
├── __init__.py              # 测试包初始化
├── conftest.py              # Pytest fixtures和配置
├── test_app_factory.py      # 测试应用工厂
├── test_api_endpoints.py    # API端点测试
└── README.md                # 本文档
```

## 🚀 快速开始

### 安装测试依赖

使用conda环境（推荐用于Windows）：

```bash
conda activate ragchatbot
pip install pytest pytest-cov pytest-asyncio pytest-mock httpx
```

或使用pip：

```bash
pip install -e ".[test]"
```

### 运行所有测试

```bash
# 从项目根目录运行
pytest

# 或从backend目录运行
cd backend
pytest
```

### 运行特定测试

```bash
# 运行API端点测试
pytest backend/tests/test_api_endpoints.py -v

# 运行特定测试类
pytest backend/tests/test_api_endpoints.py::TestQueryEndpoint -v

# 运行特定测试方法
pytest backend/tests/test_api_endpoints.py::TestQueryEndpoint::test_query_success_with_session_id -v
```

### 按标记过滤测试

```bash
# 只运行API测试
pytest -m api

# 只运行单元测试
pytest -m unit

# 只运行集成测试
pytest -m integration

# 排除慢速测试
pytest -m "not slow"
```

## 📊 代码覆盖率

### 生成覆盖率报告

```bash
# 运行测试并生成覆盖率报告
pytest --cov=backend --cov-report=html --cov-report=term-missing

# 查看HTML报告（会在 htmlcov/ 目录生成）
# Windows:
start htmlcov/index.html

# Linux/Mac:
open htmlcov/index.html
```

### 只查看覆盖率摘要

```bash
pytest --cov=backend --cov-report=term
```

## 🧪 测试类别

### 1. API端点测试 (`test_api_endpoints.py`)

测试所有FastAPI端点的功能、请求验证和错误处理。

**测试类：**
- `TestQueryEndpoint` - 测试 `/api/query` 端点
- `TestCoursesEndpoint` - 测试 `/api/courses` 端点
- `TestClearSessionEndpoint` - 测试 `/api/clear-session` 端点
- `TestMiscEndpoints` - 测试根端点和健康检查
- `TestMiddleware` - 测试CORS和中间件
- `TestAPIIntegration` - API集成测试
- `TestPerformanceAndBoundaries` - 性能和边界测试

**示例：**

```bash
# 测试查询端点
pytest backend/tests/test_api_endpoints.py::TestQueryEndpoint -v

# 测试CORS功能
pytest backend/tests/test_api_endpoints.py::TestMiddleware -v
```

### 2. 应用工厂测试 (`test_app_factory.py`)

提供独立的测试应用工厂，避免主应用的静态文件依赖问题。

**主要功能：**
- `create_test_app()` - 创建测试FastAPI应用
- 提供 `test_app` 和 `test_client` fixtures

### 3. 共享Fixtures (`conftest.py`)

提供所有测试共用的fixtures和mock对象。

**主要fixtures：**
- `mock_config` - Mock配置对象
- `mock_vector_store` - Mock向量存储
- `mock_ai_generator` - Mock AI生成器
- `mock_rag_system` - 完整的Mock RAG系统
- `sample_course_data` - 示例课程数据
- `temp_dir` - 临时测试目录

## 🎯 测试最佳实践

### 使用Fixtures

```python
def test_with_fixtures(test_client, sample_query_request):
    """使用fixtures简化测试"""
    response = test_client.post("/api/query", json=sample_query_request)
    assert response.status_code == 200
```

### 测试标记

```python
@pytest.mark.api
def test_api_endpoint():
    """标记为API测试"""
    pass

@pytest.mark.integration
def test_integration():
    """标记为集成测试"""
    pass

@pytest.mark.slow
def test_slow_operation():
    """标记为慢速测试"""
    pass
```

### Mock外部依赖

```python
def test_with_mock(mock_rag_system):
    """使用mock避免真实API调用"""
    mock_rag_system.query.return_value = ("answer", [])
    # 测试代码...
```

## 📝 编写新测试

### 1. 创建新测试文件

在 `backend/tests/` 目录下创建 `test_<module_name>.py` 文件。

### 2. 导入必要模块

```python
import pytest
from unittest.mock import Mock

@pytest.mark.unit
def test_new_feature():
    """测试新功能"""
    # 测试代码
    pass
```

### 3. 使用现有Fixtures

```python
def test_with_mock_rag(mock_rag_system):
    """使用现有的mock RAG系统"""
    result = mock_rag_system.query("test query", "session-id")
    assert result is not None
```

### 4. 添加新的Fixtures

在 `conftest.py` 中添加：

```python
@pytest.fixture
def my_new_fixture():
    """新的fixture说明"""
    return {"key": "value"}
```

## 🐛 调试测试

### 详细输出

```bash
# 显示print语句
pytest -s

# 显示详细traceback
pytest --tb=long

# 在第一个失败时停止
pytest -x

# 显示最慢的10个测试
pytest --durations=10
```

### 调试特定测试

```bash
# 使用pdb调试器
pytest --pdb

# 在失败时进入调试器
pytest --pdb --maxfail=1
```

## 🔧 常见问题

### Q: 导入错误 - 找不到backend模块

**A:** 确保从项目根目录运行pytest，或将backend目录添加到PYTHONPATH：

```bash
# Windows
set PYTHONPATH=%PYTHONPATH%;F:\case_ml\starting-ragchatbot-codebase\.trees\tesing_feature

# Linux/Mac
export PYTHONPATH=$PYTHONPATH:/path/to/project
```

### Q: 测试运行很慢

**A:** 使用并行运行测试：

```bash
# 安装pytest-xdist
pip install pytest-xdist

# 使用4个进程运行
pytest -n 4
```

### Q: Mock对象不工作

**A:** 确保在正确的位置patch：

```python
# 错误 - patch导入的位置
@patch('conftest.RAGSystem')

# 正确 - patch使用的位置
@patch('backend.app.RAGSystem')
```

### Q: 覆盖率报告不准确

**A:** 清除缓存并重新运行：

```bash
# 清除pytest缓存
pytest --cache-clear

# 清除__pycache__
find . -type d -name __pycache__ -exec rm -r {} +

# 重新运行测试
pytest --cov=backend --cov-report=html
```

## 📚 参考资源

- [Pytest文档](https://docs.pytest.org/)
- [FastAPI测试指南](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-cov文档](https://pytest-cov.readthedocs.io/)
- [unittest.mock文档](https://docs.python.org/3/library/unittest.mock.html)

## 🎓 测试命令速查表

```bash
# 基本测试
pytest                                          # 运行所有测试
pytest -v                                       # 详细输出
pytest -s                                       # 显示print输出
pytest -x                                       # 第一个失败时停止

# 特定测试
pytest backend/tests/test_api_endpoints.py      # 运行特定文件
pytest -k "test_query"                          # 运行名称匹配的测试
pytest -m api                                   # 运行特定标记

# 覆盖率
pytest --cov=backend                            # 基本覆盖率
pytest --cov=backend --cov-report=html          # HTML报告
pytest --cov=backend --cov-report=term-missing  # 显示缺失行

# 调试
pytest --pdb                                    # 失败时进入调试器
pytest --tb=long                                # 完整traceback
pytest --lf                                     # 只运行上次失败的测试
pytest --ff                                     # 先运行上次失败的测试

# 性能
pytest --durations=10                           # 显示最慢的10个测试
pytest -n 4                                     # 4个进程并行运行(需要pytest-xdist)
```

## 🤝 贡献指南

添加新测试时请遵循：

1. **命名规范**：测试文件以 `test_` 开头，测试函数以 `test_` 开头
2. **文档字符串**：每个测试函数都应有描述性的docstring
3. **标记**：为测试添加适当的标记 (`@pytest.mark.api`, `@pytest.mark.unit` 等)
4. **覆盖率**：新功能应达到至少80%的代码覆盖率
5. **独立性**：测试应该相互独立，不依赖执行顺序
