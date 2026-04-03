#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/yqlog}"
BRANCH="${BRANCH:-main}"

if [ ! -d "$APP_DIR/.git" ]; then
  echo "[deploy] 首次部署：克隆仓库到 $APP_DIR"
  git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"
echo "[deploy] 拉取最新代码: $BRANCH"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git reset --hard "origin/$BRANCH"

echo "[deploy] 构建并重启容器"
docker compose up -d --build

echo "[deploy] 完成"
