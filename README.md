# 🧠 MindFlow

MindFlow 是一款离线可用的 Web 应用，用结构化脑图的方式与大模型对话。每一次提问与回答都会落地成节点，帮助你沉淀思考过程、组织知识，并随时导出备份。

---

## 功能特性

- 画布节点：拖拽、增删、层级调整与自动布局，问题和回答一目了然
- AI 互联：内置 Echo / HTTP / Docker Model Runner / OpenAI 四类客户端，可按需切换
- 节点汇总：一键收集当前节点及子节点的问答，压缩总结后写回当前节点
- 离线持久化：Pinia + IndexedDB 自动保存，断网也能继续编辑
- 历史留存：后端 JSON 日志记录所有问答，方便审计与恢复
- 快速导出：一键导出当前脑图 JSON，便于迁移或备份

---

## 技术 & 目录

| 模块 | 技术栈 |
| --- | --- |
| 前端 | Vue 3 + Vite · Pinia · Konva.js · LocalForage |
| 后端 | FastAPI · httpx · Pydantic Settings |

```
mindflow/
├── frontend/        # Vue 应用
├── backend/         # FastAPI 服务
├── start.sh         # 一键启动脚本（可选）
└── stop.sh
```

---

## 架构快照

```
[Vue 3 Canvas UI] --Axios--> [/ask · FastAPI] --AIClient-->
  (Pinia State + IndexedDB)      (echo/http/docker/openai) --> 模型
```

---

## 快速开始

> 开始前请安装 Node.js ≥ 18 与 Python ≥ 3.10。

### 1. 首次安装依赖（只需执行一次）

```bash
# 前端依赖
cd frontend
npm install

# 后端依赖
cd ../backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 启动 / 停止服务

完成依赖安装后，可在仓库根目录使用脚本一键起停：

```bash
./start.sh   # 同时启动前后端（5173 / 8000）
./stop.sh    # 安全关闭，并清理 PID / 日志标记
```

如果需要单独运行，可依旧进入各子目录执行 `npm run dev` 或 `uvicorn main:app --reload`。项目默认把 `/api` 代理到 `http://localhost:8000`，后端会在 `backend/data/history.json` 中自动写入问答日志。

---

## 模型接入

| provider | 适用场景 | 关键字段 |
| --- | --- | --- |
| `echo` | 本地演示，无真实推理 | 无 |
| `http` | 自建 HTTP 服务 / Ollama / LM Studio | `base_url`，`headers`（可选） |
| `docker` | [Docker Model Runner](https://github.com/modelscope/modelscope/blob/master/modelscope/tools/model_runner/README.md) | `base_url`（指向 `/engines/{engine}/v1/chat/completions`），`model`，`timeout`（可选，单位秒） |
| `openai` | OpenAI 或兼容 API（Azure、OpenRouter 等） | `api_key`，`model`，`base_url`（可选），`timeout`（可选） |

示例配置（直接编辑 `backend/config.toml`，或使用环境变量覆盖）：

**Echo（内置回声）**

```toml
[ai]
provider = "echo"
```

**HTTP（Ollama / LM Studio 等自建接口）**

```toml
[ai]
provider = "http"
base_url = "http://localhost:11434/api/generate"
timeout = 60

[ai.headers]
Authorization = "Bearer custom-token"
```

**Docker Model Runner**

```toml
[ai]
provider = "docker"
base_url = "http://localhost:12434/engines/llama.cpp/v1/chat/completions"
model = "ai/gemma3"
timeout = 60  # 单位秒，可按模型加载速度自行调整
```

启动 Docker Model Runner 后，可先使用：

```bash
curl http://localhost:12434/engines/llama.cpp/v1/chat/completions \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"model":"ai/gemma3","messages":[{"role":"user","content":"你好，介绍一下你自己"}]}'
```

若需要临时覆盖配置，可在启动 FastAPI 前导出环境变量：

```bash
export MINDFLOW_PROVIDER=docker
export MINDFLOW_BASE_URL=http://localhost:12434/engines/llama.cpp/v1/chat/completions
export MINDFLOW_MODEL=ai/gemma3
```

**OpenAI / 兼容服务（默认走 `/v1/responses`，如需旧版可把 base_url 改为 `/v1/chat/completions`）**

```toml
[ai]
provider = "openai"
api_key = "sk-***"
model = "gpt-5-nano"
base_url = "https://api.openai.com/v1/responses"  # 可选
timeout = 60
```

OpenAI Python 客户端示例（与后台实现保持一致）：

```python
from openai import OpenAI

client = OpenAI()
response = client.responses.create(
    model="gpt-5-nano",
    input="Write a one-sentence bedtime story about a unicorn."
)

print(response.output_text)
```

---

## 开发提示

- `backend/config.toml` 是唯一的默认配置文件，可直接修改或使用环境变量覆盖
- `frontend/src/utils/db.ts` 负责 IndexedDB 读写，如需更换持久化策略可从此处入手
- `backend/services/ai_client.py` 统一处理模型请求与问答日志，新增 provider 也在此扩展
- `backend/routers/summary.py` 汇总节点内容并调用 AI 压缩，可用于自定义摘要策略
- 提交 PR 前建议运行 `npm run build`（前端）与 `pytest` / `ruff`（若已配置）确保质量

---

## 路线图

- [ ] 节点多选与批量操作
- [ ] 会话上下文模式
- [ ] PWA 打包与桌面安装
- [ ] AI 生成子节点推荐

欢迎 Issue / PR，一起把 MindFlow 打磨成更好用的 AI 笔记工具。🎉
