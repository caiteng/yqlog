# 语沁成长记录（轻量版）

这是一个家庭使用的轻量 Web + H5 成长记录工程：

- 快捷记录喝奶与拉臭臭
- 时间线支持删除喝奶/拉臭臭记录（含确认，防误删）
- 首页大屏看板（今日概览 + 近 30 天趋势）
- 温馨相册（上传 / 放大预览 / 删除）
- 固定口令解锁（24 小时免重复输入）

## 技术栈

- 后端：Python + Flask
- 数据库：SQLite（单机轻量）
- 前端：Vue 3（CDN 方式，局部 Vue 化）
- 图表：Chart.js
- 部署：Docker Compose + GitHub Actions(SSH)

## 本地预览（Docker，推荐）

```bash
docker compose up --build
```

> Docker 镜像构建已默认使用清华 PyPI 镜像，降低服务器与国内网络环境下 `pip install` 超时风险。

访问地址：

- 首页看板：<http://localhost:8000/>（或 <http://127.0.0.1:8000/>）
- 解锁页面：<http://127.0.0.1:8000/unlock>
- 快捷录入：<http://127.0.0.1:8000/quick>
- 相册模块：<http://127.0.0.1:8000/album>

## 服务器正式部署（仅 main）

服务器生产模式必须使用：

- `docker-compose.yml`
- `docker-compose.prod.yml`

执行命令：

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env up -d --build
```

说明：

- 自动部署只基于 `main` 分支。
- `main` 有新的 push 后，GitHub Actions 会自动 SSH 到服务器执行部署脚本。
- 支持 `workflow_dispatch` 手动触发。

## 配置说明（默认配置 + 外部覆盖）

系统启动时按以下优先级加载配置（高 -> 低）：

1. 容器内覆盖配置：`/app/config.override.yml`
2. 服务器固定路径配置：`/opt/yqlog/config.yml`
3. 项目默认配置：`config.default.yml`
4. 代码内兜底默认值：`config.py`

> 当前配置体系保持不变：`config.default.yml` + `/app/config.override.yml` + `/opt/yqlog/config.yml` + `config.py` 兜底。

服务器部署模式会把宿主机 `/opt/yqlog/config.yml` 挂载到容器 `/app/config.override.yml`。

## 服务器目录约定

- `/opt/yqlog/app`：代码目录
- `/opt/yqlog/data`：SQLite 数据目录（持久化）
- `/opt/yqlog/uploads`：上传文件目录（持久化）
- `/opt/yqlog/config.yml`：服务器外部配置文件

## 首次初始化（新服务器执行一次）

> 作用：安装 Docker / Docker Compose Plugin / Git，创建目录，克隆 main，生成 `.env`，首次启动生产 compose。

```bash
# 以 root 或 sudo 执行
mkdir -p /opt/yqlog/app
git clone https://github.com/caiteng/yqlog.git /opt/yqlog/app

REPO_URL='https://github.com/caiteng/yqlog.git' \
APP_DIR='/opt/yqlog/app' \
BRANCH='main' \
sudo bash /opt/yqlog/app/scripts/server-init.sh
```

初始化完成后，请检查并修改：

- `/opt/yqlog/app/.env`
- `/opt/yqlog/config.yml`

## 自动部署（merge/push 到 main）

工作流文件：`.github/workflows/deploy.yml`

触发方式：

1. 自动触发：push 到 `main`
2. 手动触发：GitHub Actions 页面点击 `Run workflow`

部署动作（由 GitHub Actions SSH 到服务器执行）：

```bash
cd "$DEPLOY_APP_DIR"
bash ./scripts/deploy.sh
```

`scripts/deploy.sh` 会执行：

1. 进入 `${DEPLOY_APP_DIR}`（默认 `/opt/yqlog/app`）
2. `git fetch origin/main` + `git reset --hard origin/main` 同步最新代码
3. `.env` 不存在则尝试由 `.env.example` 生成
4. 执行生产部署命令：
   `docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env up -d --build`
5. 若部署失败，自动 `git reset --hard <上一个 commit>` 回滚
6. 使用回滚版本重新执行 compose 启动，保证服务尽快恢复

## GitHub Actions Secrets

在仓库 `Settings -> Secrets and variables -> Actions` 添加：

- `DEPLOY_HOST`
- `DEPLOY_PORT`
- `DEPLOY_USER`
- `DEPLOY_SSH_KEY`
- `DEPLOY_APP_DIR`（建议 `/opt/yqlog/app`）

## 回滚说明

自动部署失败时，`scripts/deploy.sh` 会自动：

1. 回滚到部署前的 commit
2. 重新执行生产 compose 启动

如需手动回滚，可在服务器执行：

```bash
cd /opt/yqlog/app
git reflog
# 找到目标版本后，例如 HEAD@{1}
git reset --hard HEAD@{1}
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env up -d --build
```

## 项目结构（核心）

- `app.py`：路由、数据库、看板统计、相册上传删除
- `config.py`：配置加载与优先级合并逻辑
- `config.default.yml`：项目内默认配置
- `scripts/server-init.sh`：首服初始化脚本
- `scripts/deploy.sh`：自动部署脚本
- `docker-compose.yml`：本地预览默认 Compose（不挂宿主机目录）
- `docker-compose.prod.yml`：服务器正式部署覆盖 Compose（挂载持久化目录）
- `.github/workflows/deploy.yml`：GitHub Actions 自动部署
