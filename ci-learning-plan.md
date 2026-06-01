# CI/CD 实操学习计划：GitHub Actions + Buildkite

## 项目概述

通过构建一个简单的 Python REST API 项目，从零实践 GitHub Actions 和 Buildkite 两套 CI/CD 系统。

**项目选型**：Python + FastAPI + pytest + ruff（轻量快速，CI 配置简洁，构建快）

---

## 阶段一：MVP 项目搭建

**目标**：创建一个可测试、可构建的最小项目，推送到 GitHub。

### 1.1 初始化项目

- 创建项目目录，初始化 `pyproject.toml`
- 安装依赖：fastapi, uvicorn, pytest, httpx, ruff
- 创建目录结构：

```
ci-demo/
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py        # FastAPI 应用
│       └── routes.py      # 路由定义
├── tests/
│   ├── __init__.py
│   └── test_app.py        # 接口测试
├── pyproject.toml
├── requirements.txt       # 或用 requirements-dev.txt 分离
└── .gitignore
```

### 1.2 实现最小功能

- `GET /health` — 返回 `{ "status": "ok" }`
- `GET /add?a=1&b=2` — 返回 `{ "result": 3 }`
- 编写对应的 pytest 测试（用 httpx.AsyncClient 或 TestClient 发请求）

```python
# tests/test_app.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

def test_add():
    resp = client.get("/add?a=1&b=2")
    assert resp.json() == {"result": 3}
```

### 1.3 配置基础工具链

- ruff 配置（在 pyproject.toml 中）
- pyproject.toml / Makefile scripts：
  - `make lint` — 执行 `ruff check .`
  - `make format-check` — 执行 `ruff format --check .`
  - `make test` — 执行 `pytest`
  - `make build` — 打包为 wheel（`python -m build`）

```toml
# pyproject.toml 中的 ruff 配置
[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### 1.4 推送到 GitHub

- 创建 GitHub 仓库（public，方便 Actions 免费用）
- 初始化 git，首次提交，推送

---

## 阶段二：GitHub Actions 基础流水线

**目标**：在 GitHub 上实现自动化 lint → test → build 流程。

### 2.1 创建第一个 Workflow

- 创建 `.github/workflows/ci.yml`
- 触发条件：push 到 main、所有 PR
- 单 Job 实现：

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: ruff check .
      - run: ruff format --check .
      - run: pytest
```

- 推送后在 GitHub Actions 页面观察运行结果
- 故意制造一个 lint 错误（如未使用的 import），观察失败行为

### 2.2 拆分为多 Job + 依赖关系

- 拆成三个 Job：lint / test / build
- 使用 `needs` 定义依赖：build 依赖 lint 和 test 都通过
- 观察并行执行 vs 串行执行的区别

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install ruff
      - run: ruff check .
      - run: ruff format --check .

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest --tb=short

  build:
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install build
      - run: python -m build
```

### 2.3 添加矩阵测试

- 用 matrix strategy 测试多个 Python 版本（3.10, 3.11, 3.12）
- 理解 matrix 的作用和使用场景

```yaml
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -r requirements.txt
      - run: pytest
```

### 2.4 添加 Cache 加速

- 使用 `actions/cache` 缓存 pip 依赖
- 对比有无缓存的执行时间差异

```yaml
      - uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-
```

### 2.5 添加 Artifact 产物

- build 步骤产出 wheel 文件（`dist/`）
- 使用 `actions/upload-artifact` 保存构建产物
- 在 GitHub UI 中下载验证

```yaml
      - run: python -m build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
```

---

## 阶段三：GitHub Actions 进阶

**目标**：掌握实际工程中常用的 Actions 模式。

### 3.1 PR 状态检查（Branch Protection）

- 在 GitHub 仓库设置中启用 branch protection
- 要求 CI 通过才能合并 PR
- 创建一个 PR 实际体验流程

### 3.2 环境变量与 Secrets

- 添加一个需要环境变量的测试用例（如模拟外部 API key）
- 在 GitHub Settings → Secrets 中配置
- 在 workflow 中通过 `${{ secrets.XXX }}` 引用

```yaml
      - run: pytest
        env:
          API_KEY: ${{ secrets.API_KEY }}
```

### 3.3 自定义 Composite Action（可选）

- 将重复步骤（checkout + setup python + install deps）封装为 composite action
- 放在 `.github/actions/setup-python-env/action.yml`
- 在各 Job 中复用

```yaml
# .github/actions/setup-python-env/action.yml
name: "Setup Python Env"
description: "Checkout, setup Python, install deps"
inputs:
  python-version:
    default: "3.11"
runs:
  using: "composite"
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: ${{ inputs.python-version }}
    - run: pip install -r requirements.txt
      shell: bash
```

---

## 阶段四：Buildkite 基础流水线

**目标**：在 Buildkite 上实现同样的 CI 流程，理解与 GitHub Actions 的差异。

### 4.1 Buildkite 环境准备

- 注册 Buildkite 账号（免费 tier 够用）
- 创建 Organization 和第一个 Pipeline
- 关联 GitHub 仓库

### 4.2 安装 Buildkite Agent

两种方式选一种：

**方式 A：本地 Docker 运行 Agent（推荐入门）**
```bash
docker run -d \
  -e BUILDKITE_AGENT_TOKEN=xxx \
  buildkite/agent:3
```

**方式 B：本地直接安装 Agent**
```bash
brew install buildkite/buildkite/buildkite-agent
# 配置 token 后启动
buildkite-agent start
```

- 验证 Agent 在 Buildkite 控制台上线

### 4.3 创建第一个 Pipeline

- 创建 `.buildkite/pipeline.yml`：

```yaml
steps:
  - label: ":lint: Lint"
    command:
      - "pip install ruff"
      - "ruff check ."
      - "ruff format --check ."

  - label: ":test_tube: Test"
    command:
      - "pip install -r requirements.txt"
      - "pytest --tb=short"

  - wait

  - label: ":package: Build"
    command:
      - "pip install build"
      - "python -m build"
```

- 推送代码，观察 Buildkite UI 中的构建
- 理解 `wait` 步骤的作用（同步屏障）

### 4.4 理解核心差异

对比学习以下概念：

| 概念 | GitHub Actions | Buildkite |
|------|---------------|-----------|
| 执行环境 | GitHub 托管 Runner | 自托管 Agent |
| 配置位置 | `.github/workflows/` | `.buildkite/pipeline.yml` |
| 并行控制 | `needs` 依赖 | `wait` 屏障 |
| 密钥管理 | GitHub Secrets | Agent 环境变量 / Secrets 插件 |
| 扩展机制 | Marketplace Actions | Plugins |
| 触发方式 | on: push/pr/schedule | Webhook / API / Schedule |

### 4.5 使用 Buildkite Plugin

- 使用 `docker` plugin 在容器中运行步骤（不依赖 Agent 宿主环境）：

```yaml
steps:
  - label: ":test_tube: Test"
    plugins:
      - docker#v5.0.0:
          image: "python:3.11-slim"
    command:
      - "pip install -r requirements.txt"
      - "pytest"
```

---

## 阶段五：Buildkite 进阶

**目标**：掌握 Buildkite 的动态流水线和实际工程模式。

### 5.1 Dynamic Pipeline（动态流水线）

- 用脚本动态生成 pipeline YAML：

```yaml
steps:
  - label: ":pipeline: Upload"
    command: ".buildkite/generate-pipeline.sh | buildkite-agent pipeline upload"
```

- 编写 `generate-pipeline.sh`，根据变更文件动态决定跑哪些步骤
- 这是 Buildkite 最强大的特性之一，GitHub Actions 很难做到

```bash
#!/bin/bash
# .buildkite/generate-pipeline.sh
CHANGED=$(git diff --name-only HEAD~1)

cat <<YAML
steps:
YAML

if echo "$CHANGED" | grep -q "^src/"; then
cat <<YAML
  - label: ":test_tube: Test"
    command:
      - "pip install -r requirements.txt"
      - "pytest"
YAML
fi

if echo "$CHANGED" | grep -q "Dockerfile"; then
cat <<YAML
  - label: ":docker: Build Image"
    command: "docker build -t ci-demo ."
YAML
fi
```

### 5.2 Artifact 传递

- 在 test 步骤中上传覆盖率报告
- 在后续步骤中下载使用

```yaml
- label: "Test with Coverage"
  command:
    - "pip install -r requirements.txt"
    - "pytest --cov=app --cov-report=html"
  artifact_paths: "htmlcov/**/*"
```

### 5.3 并发控制 & 队列

- 配置 Agent 的 queue tag
- 让不同步骤跑在不同队列（模拟生产中的场景：测试跑在小机器、构建跑在大机器）

```yaml
steps:
  - label: "Test"
    command: "pytest"
    agents:
      queue: "small"

  - label: "Build Docker"
    command: "docker build ."
    agents:
      queue: "large"
```

---

## 阶段六：完善工程实践

**目标**：将项目补充为接近生产标准的工程项目。

### 6.1 完善项目代码

- 添加更多 API 端点（CRUD 示例，可用内存字典模拟数据库）
- 添加 Pydantic 输入校验
- 添加异常处理（FastAPI exception handlers）
- 提高测试覆盖率（`pytest --cov`）

### 6.2 添加 Docker 支持

- 编写 Dockerfile（多阶段构建）：

```dockerfile
FROM python:3.11-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS production
COPY src/ ./src/
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- 在 CI 中构建镜像并推送到 GitHub Container Registry
- Buildkite 中同样添加 docker build 步骤

```yaml
# GitHub Actions docker build + push
  deploy:
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:latest
```

### 6.3 添加部署步骤（模拟）

- GitHub Actions：添加 deploy job（输出 "deploying to staging..."）
- Buildkite：添加 `block` 步骤（手动审批后部署）

```yaml
# Buildkite 手动审批
- block: ":rocket: Deploy to Production?"

- label: ":shipit: Deploy"
  command: "echo 'Deploying...'"
```

### 6.4 Monorepo 模式（可选扩展）

- 添加第二个子项目（如一个简单的 CLI 工具或数据处理脚本）
- 实现路径过滤：只有相关目录变更才触发对应 CI
- GitHub Actions: `paths` filter
- Buildkite: 动态 pipeline 按路径判断

```yaml
# GitHub Actions paths filter
on:
  push:
    paths:
      - "api/**"
      - ".github/workflows/api-ci.yml"
```

---

## 学习检查清单

完成后你应该能回答：

- [ ] GitHub Actions 的 workflow/job/step 三层结构是什么？
- [ ] `needs` 和 `if` 如何控制执行流？
- [ ] Matrix strategy 适合什么场景？
- [ ] Buildkite Agent 的角色是什么？为什么要自托管？
- [ ] `wait` 和 `block` 的区别？
- [ ] Dynamic pipeline 解决了什么问题？
- [ ] 两套系统各自的优势场景是什么？
- [ ] pip cache 和 venv 缓存策略有什么区别？
- [ ] Python 项目中 pyproject.toml 如何统一管理工具配置？

---

## 时间预估

| 阶段 | 预计耗时 |
|------|---------|
| 阶段一：MVP 搭建 | 20-30 分钟 |
| 阶段二：GitHub Actions 基础 | 1-2 小时 |
| 阶段三：GitHub Actions 进阶 | 1 小时 |
| 阶段四：Buildkite 基础 | 1-2 小时 |
| 阶段五：Buildkite 进阶 | 1-2 小时 |
| 阶段六：工程完善 | 2-3 小时 |

**总计约 7-10 小时**，可分 2-3 天完成。

---

## 工具链速查

| 用途 | 工具 | 命令 |
|------|------|------|
| Lint | ruff | `ruff check .` |
| Format | ruff | `ruff format --check .` |
| 测试 | pytest | `pytest --tb=short` |
| 覆盖率 | pytest-cov | `pytest --cov=app --cov-report=html` |
| 打包 | build | `python -m build` |
| 运行 | uvicorn | `uvicorn app.main:app --reload` |
| 类型检查（可选） | mypy | `mypy src/` |
