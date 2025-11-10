#!/usr/bin/env bash
set -euo pipefail

if [ -z "${BASH_VERSION:-}" ]; then
  exec bash "$0" "$@"
fi

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$DIR/.mindflow.pids"
LOG_DIR="$DIR/.logs"
FRONT_LOG="$LOG_DIR/frontend.log"
BACK_LOG="$LOG_DIR/backend.log"
FRONT_URL="http://localhost:5173"
BACK_URL="http://localhost:8000"
cleanup_has_run=0

mkdir -p "$LOG_DIR"
touch "$FRONT_LOG" "$BACK_LOG"

timestamp() {
  date "+%Y-%m-%d %H:%M:%S"
}

log() {
  printf '[MindFlow %s] %s\n' "$(timestamp)" "$*" >&2
}

show_log_tail() {
  local log_file="$1"
  local label="$2"
  if [[ ! -f "$log_file" ]]; then
    log "${label}：日志文件 ${log_file} 不存在或尚未生成。"
    return
  fi
  log "${label}：最近 40 行日志如下 ↓"
  tail -n 40 "$log_file" | sed 's/^/    /'
}

cleanup() {
  local exit_status=${1:-$?}
  if [[ "${cleanup_has_run:-0}" -eq 1 ]]; then
    return
  fi
  cleanup_has_run=1
  log "触发清理流程（状态码：${exit_status}）..."
  if [[ -n "${BACK_PID:-}" ]] && kill -0 "$BACK_PID" 2>/dev/null; then
    kill "$BACK_PID" 2>/dev/null || true
  fi
  if [[ -n "${FRONT_PID:-}" ]] && kill -0 "$FRONT_PID" 2>/dev/null; then
    kill "$FRONT_PID" 2>/dev/null || true
  fi
  rm -f "$PID_FILE"
}

fail() {
  log "错误：$*"
  cleanup 1
  exit 1
}

if [[ -f "$PID_FILE" ]]; then
  fail "检测到已运行的实例（${PID_FILE} 存在），请先执行 ./stop.sh"
fi

BACKEND_PYTHON="python3"
if [[ -x "$DIR/backend/.venv/bin/python" ]]; then
  BACKEND_PYTHON="$DIR/backend/.venv/bin/python"
fi

if ! command -v "$BACKEND_PYTHON" >/dev/null 2>&1; then
  fail "未找到 Python3，请先安装或检查 backend/.venv"
fi

if ! "$BACKEND_PYTHON" -m uvicorn --version >/dev/null 2>&1; then
  fail "Python 环境中未安装 uvicorn，请先在 backend 执行 'pip install -r requirements.txt'"
fi

if ! command -v npm >/dev/null 2>&1; then
  fail "未找到 npm，请安装 Node.js (>=18)"
fi

if [[ ! -d "$DIR/frontend/node_modules" ]]; then
  fail "未检测到 frontend/node_modules，请先进入 frontend 执行 'npm install'"
fi

check_port_free() {
  local port="$1"
  local service="$2"
  if command -v lsof >/dev/null 2>&1; then
    local listeners
    listeners="$(lsof -ti tcp:"$port" || true)"
    if [[ -n "$listeners" ]]; then
      log "${service} 需要使用端口 ${port}，但当前由进程 ${listeners} 占用。"
      fail "端口 ${port} 被占用，请结束上述进程后重试。"
    fi
  else
    log "提示：系统缺少 lsof，无法提前检测 ${service} 的端口 ${port} 是否占用。"
  fi
}

check_port_free 8000 "FastAPI 后端"
check_port_free 5173 "Vite 前端"

echo -e "\n===== $(timestamp) =====" >>"$BACK_LOG"
echo -e "\n===== $(timestamp) =====" >>"$FRONT_LOG"

run_backend() {
  log "启动 FastAPI 后端（端口 8000）..."
  (
    cd "$DIR/backend"
    exec "$BACKEND_PYTHON" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
  ) >>"$BACK_LOG" 2>&1 &
  echo $!
}

run_frontend() {
  log "启动 Vite 前端（端口 5173）..."
  (
    cd "$DIR/frontend"
    exec npm run dev -- --host
  ) >>"$FRONT_LOG" 2>&1 &
  echo $!
}

ensure_running() {
  local name="$1" pid="$2" log_file="$3"
  for _ in $(seq 1 10); do
    if kill -0 "$pid" 2>/dev/null; then
      log "${name} 已在后台运行 (PID ${pid})。"
      return 0
    fi
    sleep 0.5
  done
  show_log_tail "$log_file" "$name"
  fail "${name} 启动失败，请参考上方日志（${log_file}）。"
}

trap 'cleanup $?' ERR

BACK_PID=$(run_backend)
FRONT_PID=$(run_frontend)

ensure_running "后端" "$BACK_PID" "$BACK_LOG"
ensure_running "前端" "$FRONT_PID" "$FRONT_LOG"

cat >"$PID_FILE" <<PID
BACKEND=$BACK_PID
FRONTEND=$FRONT_PID
PID

log "启动成功！"
cat <<INFO
──────────────────────────────────────
MindFlow 已启动：
  ▸ 后端：${BACK_URL} （健康检查：${BACK_URL}/health）
    PID: ${BACK_PID}  日志：${BACK_LOG}
  ▸ 前端：${FRONT_URL}
    PID: ${FRONT_PID}  日志：${FRONT_LOG}

请在浏览器访问：$FRONT_URL
使用 ./stop.sh 可一键停止。
──────────────────────────────────────
INFO
