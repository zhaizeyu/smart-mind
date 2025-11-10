#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd)"
PID_FILE="$DIR/.mindflow.pids"
BACKEND_PORT=8000
FRONTEND_PORT=5173
found_instance=0

if [[ -f "$PID_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$PID_FILE"
  found_instance=1
else
  echo "未找到 PID 文件，尝试通过端口扫描正在运行的进程..." >&2
fi

stop_proc() {
  local name="$1"
  local pid="$2"
  if [[ -z "$pid" ]]; then
    return
  fi
  if kill -0 "$pid" >/dev/null 2>&1; then
    echo "停止 $name (PID $pid)"
    kill "$pid" >/dev/null 2>&1 || true
    wait "$pid" 2>/dev/null || true
  else
    echo "$name (PID $pid) 已不在运行"
  fi
}

stop_by_port() {
  local name="$1"
  local port="$2"
  if ! command -v lsof >/dev/null 2>&1; then
    echo "无法检测端口 $port（系统无 lsof）。" >&2
    return
  fi
  local pids
  pids="$(lsof -ti tcp:"$port" || true)"
  if [[ -z "$pids" ]]; then
    return
  fi
  echo "$name 使用的端口 $port 仍被占用，尝试终止进程：$pids"
  for pid in $pids; do
    stop_proc "$name" "$pid"
  done
  found_instance=1
}

if [[ -n "${BACKEND:-}" ]]; then
  stop_proc "后端" "${BACKEND}"
  found_instance=1
fi

if [[ -n "${FRONTEND:-}" ]]; then
  stop_proc "前端" "${FRONTEND}"
  found_instance=1
fi

stop_by_port "后端" "$BACKEND_PORT"
stop_by_port "前端" "$FRONTEND_PORT"

if [[ $found_instance -eq 0 ]]; then
  echo "没有检测到需要停止的 MindFlow 进程。"
  exit 0
fi

rm -f "$PID_FILE" 2>/dev/null || true
echo "MindFlow 已全部停止。"
