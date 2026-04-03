#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/yqlog/app}"
BRANCH="${BRANCH:-main}"
REPO_URL="${REPO_URL:-}"

if [ ! -d "$APP_DIR" ]; then
  echo "[deploy] app 目录不存在: $APP_DIR"
  echo "[deploy] 请先执行 scripts/server-init.sh"
  exit 1
fi

cd "$APP_DIR"

if [ ! -d .git ]; then
  if [ -z "$REPO_URL" ]; then
    echo "[deploy] 目录不是 git 仓库，且未提供 REPO_URL"
    exit 1
  fi
  echo "[deploy] 首次拉代码到 $APP_DIR"
  rm -rf "$APP_DIR"
  git clone "$REPO_URL" "$APP_DIR"
  cd "$APP_DIR"
fi

PREV_COMMIT="$(git rev-parse HEAD 2>/dev/null || true)"

echo "[deploy] 拉取最新代码: $BRANCH"
git fetch --prune origin "$BRANCH"
git checkout "$BRANCH"
git reset --hard "origin/$BRANCH"

if [ ! -f .env ]; then
  echo "[deploy] 缺少 .env，尝试从 .env.example 创建"
  cp .env.example .env
fi

echo "[deploy] 开始构建并启动容器"
if docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env up -d --build; then
  echo "[deploy] 部署成功: $(git rev-parse --short HEAD)"
  exit 0
fi

if [ -n "$PREV_COMMIT" ]; then
  echo "[deploy] 部署失败，回滚到上一版本: ${PREV_COMMIT}"
  git reset --hard "$PREV_COMMIT"
  docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env up -d --build
fi

echo "[deploy] 已完成回滚"
