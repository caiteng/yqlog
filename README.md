# 语沁成长记录（轻量版）

一个轻量级 Web + H5 工程，用于记录女儿语沁的成长信息：

- 身高 / 体重 / 头围
- 成长照片上传
- 首页大屏统计（趋势图 + 核心指标）
- 成长轨迹时间线
- 手机端（H5）录入
- 口令解锁（24 小时免输）

## 技术栈

- Python + Flask（轻量）
- SQLite（单文件数据库，资源占用低）
- Vue 3（CDN 方式，局部增强交互，无需复杂构建）
- Chart.js（趋势图）

## 启动（本地）

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

启动后访问：

- 首页：<http://127.0.0.1:8000/>
- 录入解锁：<http://127.0.0.1:8000/unlock>
- H5 提交：<http://127.0.0.1:8000/submit>

## 配置说明

配置集中在 `config.py`：

- `SECRET_KEY`：Flask Session 密钥
- `ACCESS_PASSWORD`：录入固定口令（当前默认：`无敌可爱语沁`）
- `SESSION_DAYS`：解锁有效天数（默认 1 天）
- `DATABASE_PATH`：SQLite 文件路径
- `UPLOAD_FOLDER`：上传目录

## SQLite 说明

继续采用 SQLite，初始化时会自动设置：

- `PRAGMA journal_mode=WAL;`
- `PRAGMA synchronous=NORMAL;`
- `PRAGMA foreign_keys=ON;`

并创建基础索引，适合当前低频录入、单机部署场景。

## 目录说明

- `app.py`: 主程序（路由、数据库、上传处理、解锁拦截）
- `config.py`: 轻量配置文件
- `templates/`: 页面模板（含 `/unlock`、`/submit`）
- `static/js/submit-vue.js`: 提交页 Vue 交互
- `static/js/unlock-vue.js`: 解锁页 Vue 交互
- `static/css/main.css`: 样式

## 自动部署到服务器（已支持）

项目包含 Docker + GitHub Actions 自动部署方案：

- `Dockerfile` + `docker-compose.yml`：容器化运行应用
- `.github/workflows/deploy.yml`：当 `main` 分支有新提交时，自动 SSH 到服务器执行部署
- `scripts/deploy.sh`：服务器端拉取最新代码并重启容器
