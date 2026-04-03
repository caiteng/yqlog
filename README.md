# 语沁成长记录（轻量版）

这是一个家庭使用的轻量 Web + H5 成长记录工程：

- 快捷记录喝奶与拉臭臭
- 首页大屏看板（今日概览 + 近 30 天趋势）
- 温馨相册（上传 / 预览 / 删除）
- 固定口令解锁（24 小时免重复输入）

## 技术栈

- 后端：Python + Flask
- 数据库：SQLite（单机轻量）
- 前端：Vue 3（CDN 方式，局部 Vue 化）
- 图表：Chart.js
- 部署：Docker Compose + GitHub Actions(SSH)

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

启动后访问：

- 首页看板：<http://127.0.0.1:8000/>
- 解锁页面：<http://127.0.0.1:8000/unlock>
- 快捷录入：<http://127.0.0.1:8000/quick>
- 相册模块：<http://127.0.0.1:8000/album>

## 配置说明

可通过环境变量配置（推荐），默认值在 `config.py`：

- `FLASK_SECRET_KEY`：Session 密钥
- `ACCESS_PASSWORD`：录入口令（默认 `无敌可爱语沁`）
- `SESSION_DAYS`：Session 有效天数（默认 1 天）
- `DATABASE_PATH`：SQLite 路径
- `UPLOAD_FOLDER`：上传目录

可复制 `.env.example` 到 `.env` 后按需修改。

## 服务器目录约定（自动部署）

- `/opt/yqlog/app`：代码目录
- `/opt/yqlog/data`：SQLite 数据目录（持久化）
- `/opt/yqlog/uploads`：上传文件目录（持久化）

## 首次初始化（手工执行一次）

> 在新服务器上执行，用于安装 Docker/Compose、建目录、拉代码、生成 `.env`。

```bash
# 以 root 或 sudo 执行
cd /opt/yqlog/app 2>/dev/null || true

# 若目录还没有仓库，可临时先拉一份后执行
# git clone https://github.com/caiteng/yqlog.git /opt/yqlog/app

REPO_URL='https://github.com/caiteng/yqlog.git' \
APP_DIR='/opt/yqlog/app' \
DATA_DIR='/opt/yqlog/data' \
UPLOADS_DIR='/opt/yqlog/uploads' \
BRANCH='main' \
bash /opt/yqlog/app/scripts/server-init.sh
```

执行后请编辑 `/opt/yqlog/app/.env`，至少修改：

- `FLASK_SECRET_KEY`
- `ACCESS_PASSWORD`

## 自动部署（merge/push main 自动触发）

工作流：`.github/workflows/deploy.yml`

触发条件：

- push 到 `main`
- 手工触发（workflow_dispatch）

工作流会 SSH 到服务器并执行：

```bash
bash /opt/yqlog/app/scripts/deploy.sh
```

`deploy.sh` 会：

1. `git fetch + reset --hard origin/main`
2. `docker compose up -d --build`
3. 若失败，自动回滚到上一个 commit 并再次启动

## GitHub Secrets

在仓库 `Settings -> Secrets and variables -> Actions` 中添加：

- `DEPLOY_HOST`：服务器公网 IP 或域名
- `DEPLOY_PORT`：SSH 端口（如 `22`）
- `DEPLOY_USER`：SSH 用户名（如 `root` 或 `ubuntu`）
- `DEPLOY_SSH_KEY`：用于登录服务器的私钥内容（建议专用部署密钥）
- `DEPLOY_APP_DIR`：部署目录（建议 `/opt/yqlog/app`）

## 项目结构（核心）

- `app.py`：路由、数据库、看板统计、相册上传删除
- `config.py`：轻量配置
- `scripts/server-init.sh`：首服初始化脚本
- `scripts/deploy.sh`：自动部署脚本
- `docker-compose.yml`：容器与数据卷定义
- `.github/workflows/deploy.yml`：GitHub Actions 自动部署

## 数据表

启动应用会自动初始化以下表：

- `milk_records`：喝奶记录（`record_time`, `milk_ml`）
- `poop_records`：拉臭臭记录（`record_time`, `poop_status`）
- `album_photos`：相册图片（`image_path`, `created_at`）

并设置 SQLite 参数：

- `PRAGMA journal_mode=WAL;`
- `PRAGMA synchronous=NORMAL;`
- `PRAGMA foreign_keys=ON;`
