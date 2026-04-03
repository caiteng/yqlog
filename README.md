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

## 本地预览（Docker，推荐）

```bash
docker compose up --build
```

访问地址：

- 首页看板：<http://localhost:8000/>（或 <http://127.0.0.1:8000/>）
- 解锁页面：<http://127.0.0.1:8000/unlock>
- 快捷录入：<http://127.0.0.1:8000/quick>
- 相册模块：<http://127.0.0.1:8000/album>

说明：

- 本地模式默认不挂载宿主机目录（`data/uploads/config`）。
- 主要用于快速预览页面和交互。
- 停掉容器后数据可丢失，这是预期行为。

## 服务器正式部署

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env up -d --build
```

说明：

- 服务器模式会挂载 `/opt/yqlog/data`、`/opt/yqlog/uploads`、`/opt/yqlog/config.yml`。
- 容器重建后，SQLite 数据与上传图片会持久化。

## 配置说明（默认配置 + 外部覆盖）

系统启动时会按以下优先级加载配置（高 -> 低）：

1. 容器内覆盖配置：`/app/config.override.yml`
2. 服务器固定路径配置：`/opt/yqlog/config.yml`
3. 项目默认配置：`config.default.yml`
4. 代码内兜底默认值：`config.py`

也就是说：只要服务器上配置文件存在，就会覆盖项目默认配置；若外部配置不存在，系统仍可使用项目内默认配置正常运行。

### 配置文件结构（YAML）

```yaml
app:
  app_name: "语沁成长记录"
  secret_key: "please-change-me"

security:
  access_password: "无敌可爱语沁"
  session_days: 1

server:
  host: "0.0.0.0"
  port: 8000

database:
  sqlite_path: "./data/yqlog.db"

storage:
  upload_dir: "./uploads"
  album_max_photos: 200
  max_image_size_bytes: 10485760
  max_content_length: 62914560
  allowed_extensions: [png, jpg, jpeg, webp, gif]

stats:
  milk_days: 30
  poop_days: 30
```

### 服务器如何修改配置

1. 在宿主机编辑 `/opt/yqlog/config.yml`（建议只写要覆盖的项）。
2. 若使用服务器部署 Compose（`-f docker-compose.yml -f docker-compose.prod.yml`），配置会挂载到容器内 `/app/config.override.yml` 并自动生效优先级最高。

### 修改配置后是否需要重启容器

需要。配置在应用启动时加载，修改后请执行：

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env up -d
```


## 可复用 API（为后续小程序预留）

当前已提供 `/api/v1` 能力，Web/H5 与未来小程序都可复用：

- `GET /api/v1/dashboard`：首页统计数据
- `POST /api/v1/records/milk`：新增喝奶记录
- `POST /api/v1/records/poop`：新增拉臭臭记录
- `GET /api/v1/album/photos`：相册列表 + 容量元信息
- `POST /api/v1/album/photos`：上传照片（后端校验 200 张上限）
- `DELETE /api/v1/album/photos/<photo_id>`：删除照片（删库 + 删物理文件）

相册限制策略（可配置）：

- 相册最多 200 张（后端强校验）
- 单张图片默认最大 10MB（通过配置文件调整）

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
BRANCH='main' \
bash /opt/yqlog/app/scripts/server-init.sh
```

执行后请编辑 `/opt/yqlog/config.yml`，至少修改：

- `app.secret_key`
- `security.access_password`

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
2. `docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env up -d --build`
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
- `config.py`：配置加载与优先级合并逻辑
- `config.default.yml`：项目内默认配置
- `scripts/server-init.sh`：首服初始化脚本
- `scripts/deploy.sh`：自动部署脚本
- `docker-compose.yml`：本地预览默认 Compose（不挂宿主机目录）
- `docker-compose.prod.yml`：服务器正式部署覆盖 Compose（挂载持久化目录）
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
