# MindFlow

> 用思维导图和本地/云端大模型对话，随手记录每次问答。

## 功能亮点

- 拖拽式脑图：节点可自由移动、重排层级，父子关系随拖放即时更新
- AI 双向协作：向模型提问、汇总节点答案、自动生成 2 个发散子问题
- 双重持久化：前端数据存入 IndexedDB，后端同步 `backend/data/mindmap.json`
- 一键脚本：`start.sh` / `stop.sh` 同时管理前后端
- 可控回答风格：`answer_style` 提示词影响所有模型回复，默认“简要回答”

## 技术栈

| 模块 | 说明 |
| --- | --- |
| 前端 | Vue 3 + Vite · Pinia · Konva.js · LocalForage |
| 后端 | FastAPI · httpx · Pydantic Settings |

目录结构：

```
mindflow/
├── frontend/    # Vue 应用
├── backend/     # FastAPI 服务
├── start.sh     # 一键启动
└── stop.sh
```

## 快速开始

```bash
# 安装依赖
cd frontend && npm install
cd ../backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# 启动 / 停止（根目录执行）
./start.sh
./stop.sh
```

开发时也可以分别运行 `npm run dev` 和 `uvicorn main:app --reload`，前端已通过 Vite 代理把 `/api` 指向 `http://localhost:8000`。

## 配置大模型

`backend/config.toml` 是唯一的配置文件，也可用 `MINDFLOW_` 环境变量覆盖。所有 provider 都支持 `answer_style`（提示词）影响回复风格。

| provider | 适用场景 | 关键字段 |
| --- | --- | --- |
| `echo` | 本地演示，无真实推理 | `answer_style`（可选） |
| `http` | 自建 HTTP 接口 / Ollama / LM Studio | `base_url`、`headers`（可选）、`timeout`、`answer_style` |
| `docker` | ModelScope Docker Model Runner | `base_url`、`model`、`timeout`、`answer_style` |
| `openai` | OpenAI / Azure / OpenRouter 等 | `api_key`、`model`、`base_url`（可选）、`timeout`、`answer_style` |

示例（Docker 模式）：

```toml
[ai]
provider = "docker"
base_url = "http://localhost:12434/engines/llama.cpp/v1/chat/completions"
model = "ai/gemma3"
timeout = 60
answer_style = "你是一名简明扼要的助理，请用 2-3 句话直接回答用户问题。"
```

若要临时覆盖配置：

```bash
export MINDFLOW_PROVIDER=docker
export MINDFLOW_BASE_URL=http://localhost:12434/engines/llama.cpp/v1/chat/completions
export MINDFLOW_MODEL=ai/gemma3
export MINDFLOW_ANSWER_STYLE="更具象、有例子的回答"
```

OpenAI Python SDK 对应调用：

```python
from openai import OpenAI
client = OpenAI()
response = client.responses.create(
    model="gpt-5-nano",
    input="Write a one-sentence bedtime story about a unicorn."
)
print(response.output_text)
```

## 开发提示

- `frontend/src/stores/useMindStore.ts` 负责整个脑图数据结构，新增行为请在此统一管理
- `frontend/src/components/MindMapCanvas.vue` 处理拖拽/连线逻辑
- `backend/services/ai_client.py` 抽象了所有 provider 的调用与回答风格提示
- `backend/routers/summary.py` / `backend/routers/generate.py` 分别提供“节点汇总”和“AI 生成子节点”接口
- `backend/routers/mindmap.py` 负责脑图的服务端存储，防止浏览器缓存清空后数据丢失
- 提交 PR 前建议运行 `npm run build`（前端）与适用的 Python 测试 / Lint

欢迎 Issue / PR，让 MindFlow 成为更好用的脑图式 AI 笔记工具。🎉
