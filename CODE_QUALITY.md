# 代码质量工具指南

本项目已配置完整的代码质量工具链，确保代码风格统一、质量可控。

## 工具概览

### Black - 代码格式化
- **作用**：自动格式化 Python 代码，确保统一的代码风格
- **配置**：pyproject.toml 中的 `[tool.black]` 部分
- **特点**：
  - 行长度：88 字符
  - 目标版本：Python 3.13
  - 自动排除 chroma_db、.venv 等目录

### isort - 导入排序
- **作用**：自动排序和格式化 import 语句
- **配置**：pyproject.toml 中的 `[tool.isort]` 部分
- **特点**：
  - 使用 Black 兼容配置
  - 多行导入输出模式
  - 自动跳过 chroma_db、venv 目录

### flake8 - 代码检查
- **作用**：检查代码风格问题、语法错误和潜在 bug
- **配置**：.flake8 文件
- **特点**：
  - 最大行长度：88（与 Black 一致）
  - 忽略与 Black 冲突的规则（E203, W503）
  - 最大复杂度：10
  - 自动忽略 `__init__.py` 中的 F401（未使用导入）

### pre-commit - Git 钩子
- **作用**：在 Git 提交前自动运行质量检查
- **配置**：.pre-commit-config.yaml
- **包含钩子**：
  - 尾随空格清理
  - 文件末尾换行符
  - YAML/JSON/TOML 格式检查
  - Black 格式化
  - isort 导入排序
  - flake8 代码检查

## 快速开始

### 1. 安装工具

**使用 conda 环境（推荐）：**
```bash
conda activate ragchatbot
pip install black flake8 isort pre-commit
```

**或使用项目依赖：**
```bash
pip install -e ".[dev]"
```

### 2. 格式化代码

**自动格式化整个代码库：**
```bash
# Windows
format_code.bat

# Unix/Linux/Mac
./format_code.sh
```

**手动格式化：**
```bash
# 只运行 isort
isort backend

# 只运行 Black
black backend

# 同时运行
isort backend && black backend
```

### 3. 检查代码质量

**运行完整质量检查：**
```bash
# Windows
quality_check.bat

# Unix/Linux/Mac
./quality_check.sh
```

**手动检查：**
```bash
# 检查（不修改）
isort --check-only backend
black --check backend
flake8 backend
```

### 4. 设置 Git 钩子（可选）

启用自动检查，在每次 commit 前运行：
```bash
pre-commit install
```

测试 pre-commit 配置：
```bash
pre-commit run --all-files
```

## 工作流建议

### 日常开发
1. 编写代码
2. 运行 `format_code.bat`（或 .sh）自动格式化
3. 运行 `quality_check.bat`（或 .sh）检查质量
4. 修复任何 flake8 警告
5. 提交代码

### 代码审查前
```bash
# 确保所有代码已格式化
format_code.bat

# 确保通过所有检查
quality_check.bat

# 如果安装了 pre-commit
pre-commit run --all-files
```

## 常见问题

### Q: Black 修改了我的代码格式怎么办？
A: Black 是固执己见的格式化工具，这是设计目标。接受它的格式化可以避免团队成员之间的格式争议。

### Q: flake8 报告的错误如何修复？
A: 常见错误：
- **F401 (未使用导入)**：删除未使用的导入
- **E501 (行太长)**：Black 已配置 88 字符，通常会自动处理
- **E302/E303 (空行)**：Black 会自动处理
- **W503 (二元运算符前换行)**：已在配置中忽略

### Q: 为什么 isort 和 Black 都要运行？
A: isort 专门处理 import 语句的排序，Black 处理整体代码格式。两者互补，isort 配置为与 Black 兼容。

### Q: pre-commit 太慢怎么办？
A: 可以临时跳过：
```bash
git commit --no-verify
```
但不建议频繁使用，会降低代码质量。

## 配置文件说明

### pyproject.toml
包含 Black 和 isort 的配置，以及项目依赖定义。

### .flake8
包含 flake8 的检查规则配置。

### .pre-commit-config.yaml
定义 Git 提交前自动运行的检查和格式化操作。

## CI/CD 集成

如果使用 CI/CD（如 GitHub Actions），可以添加质量检查步骤：

```yaml
- name: Check code quality
  run: |
    pip install black flake8 isort
    isort --check-only backend
    black --check backend
    flake8 backend
```

## 团队协作建议

1. **统一工具版本**：确保团队成员使用相同版本的工具
2. **启用 pre-commit**：建议所有开发者安装 pre-commit hooks
3. **定期更新**：定期更新工具到最新稳定版本
4. **代码审查**：除了工具检查，人工审查仍然重要

## 更多资源

- [Black 文档](https://black.readthedocs.io/)
- [isort 文档](https://pycqa.github.io/isort/)
- [flake8 文档](https://flake8.pycqa.org/)
- [pre-commit 文档](https://pre-commit.com/)
