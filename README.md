# 语沁成长记录（轻量版）

这是一个家庭使用的轻量 Web + H5 成长记录工程：

- 快捷记录喝奶与拉臭臭
- 首页大屏看板（今日概览 + 近 30 天趋势）
- 温馨相册（上传 / 放大预览 / 删除）
- 固定口令解锁（24 小时免重复输入）

## 技术栈

- 后端：Python + Flask
- 数据库：SQLite（单机轻量）
- 前端：Vue 3（CDN 方式，局部 Vue 化）
- 图表：Chart.js
- 部署：Docker Compose + GitHub Actions(SSH)

## Docker 运行方式（本地 + 服务器）

本项目采用 **1 个基础 compose + 1 个生产覆盖 compose**：

- `docker-compose.yml`：本地默认预览（不强制挂载宿主机目录）
- `docker-compose.prod.yml`：服务器覆盖（追加数据卷与外部配置挂载）

---

### 模式 A：本地 Mac 快速预览

一条命令即可启动：

```bash
docker compose up --build
```

访问地址：

- <http://127.0.0.1:8000/>

特点：

- 不需要提前创建 `/opt/yqlog/*` 目录
- 不强制挂载宿主机数据目录
- 默认使用容器内 `/app/data`、`/app/uploads`
- 适合快速预览页面与交互（容器重建后数据可能丢失）

---

### 模式 B：服务器正式部署

推荐命令：

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

`docker-compose.prod.yml` 默认会挂载：

- `${DATA_DIR:-/opt/yqlog/data} -> /app/data`
- `${UPLOADS_DIR:-/opt/yqlog/uploads} -> /app/uploads`
- `${CONFIG_FILE:-/opt/yqlog/config.yml} -> /app/config.override.yml (ro)`

这样可以保证：

- SQLite 数据持久化在宿主机
- 上传文件持久化在宿主机
- 容器重建后数据不丢

> 修改服务器配置文件后，需要重启容器使配置生效：
>
> ```bash
> docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
> ```

## 配置系统（覆盖优先级）

配置优先级从高到低：

1. **服务器外部配置文件**（默认 `/app/config.override.yml`，通常由宿主机 `/opt/yqlog/config.yml` 挂载进来）
2. **项目默认配置文件**（`config.default.yml`）
3. **代码默认值**（`config.py` 里的 `CODE_DEFAULTS`）

即：

- 如果服务器外部配置存在，优先使用它
- 否则回退到项目默认配置
- 若默认配置也缺失，最后使用代码兜底值

### 可配置项（示例）

- `SECRET_KEY`
- `ACCESS_PASSWORD`
- `SESSION_DAYS`
- `DATABASE_PATH`
- `UPLOAD_FOLDER`
- `ALBUM_MAX_PHOTOS`
- `MAX_IMAGE_SIZE_BYTES`
- `MAX_CONTENT_LENGTH`
- `ALLOWED_EXTENSIONS`

### 服务器配置样例（`/opt/yqlog/config.yml`）

```yaml
SECRET_KEY: "replace-with-strong-random"
ACCESS_PASSWORD: "请改成你的口令"
SESSION_DAYS: 3
DATABASE_PATH: /app/data/yqlog.db
UPLOAD_FOLDER: /app/uploads
ALBUM_MAX_PHOTOS: 300
MAX_IMAGE_SIZE_BYTES: 15728640
MAX_CONTENT_LENGTH: 62914560
ALLOWED_EXTENSIONS: ["png", "jpg", "jpeg", "webp", "gif"]
```

## 本地 Python 直接运行（可选）

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## 可复用 API（为后续小程序预留）

当前已提供 `/api/v1` 能力，Web/H5 与未来小程序都可复用：

- `GET /api/v1/dashboard`：首页统计数据
- `POST /api/v1/records/milk`：新增喝奶记录
- `POST /api/v1/records/poop`：新增拉臭臭记录
- `GET /api/v1/album/photos`：相册列表 + 容量元信息
- `POST /api/v1/album/photos`：上传照片（后端校验上限）
- `DELETE /api/v1/album/photos/<photo_id>`：删除照片（删库 + 删物理文件）

## 服务器目录约定（自动部署）

- `/opt/yqlog/app`：代码目录
- `/opt/yqlog/data`：SQLite 数据目录（持久化）
- `/opt/yqlog/uploads`：上传文件目录（持久化）
- `/opt/yqlog/config.yml`：服务器配置文件（推荐）

## 首次初始化（手工执行一次）

```bash
REPO_URL='https://github.com/caiteng/yqlog.git' \
APP_DIR='/opt/yqlog/app' \
DATA_DIR='/opt/yqlog/data' \
UPLOADS_DIR='/opt/yqlog/uploads' \
BRANCH='main' \
bash /opt/yqlog/app/scripts/server-init.sh
```

执行后请编辑 `/opt/yqlog/app/.env`，确认目录变量与配置文件路径：

- `DATA_DIR`
- `UPLOADS_DIR`
- `CONFIG_FILE`

## 自动部署（merge/push main 自动触发）

工作流：`.github/workflows/deploy.yml`

`deploy.sh` 会：

1. `git fetch + reset --hard origin/main`
2. `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`
3. 若失败，自动回滚到上一个 commit 并再次启动

## 项目结构（核心）

- `app.py`：路由、数据库、看板统计、相册上传删除
- `config.py`：配置加载（覆盖优先级）
- `config.default.yml`：项目默认配置
- `docker-compose.yml`：本地预览默认配置
- `docker-compose.prod.yml`：服务器部署覆盖配置
- `scripts/server-init.sh`：首服初始化脚本
- `scripts/deploy.sh`：自动部署脚本

## 数据表

启动应用会自动初始化以下表：

- `milk_records`：喝奶记录（`record_time`, `milk_ml`）
- `poop_records`：拉臭臭记录（`record_time`, `poop_status`）
- `album_photos`：相册图片（`image_path`, `created_at`）
