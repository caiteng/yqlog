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

配置在 `config.py`：

- `SECRET_KEY`：Session 密钥
- `ACCESS_PASSWORD`：录入口令（默认 `无敌可爱语沁`）
- `SESSION_DAYS`：Session 有效天数（默认 1 天）
- `DATABASE_PATH`：SQLite 路径
- `UPLOAD_FOLDER`：上传目录

## 数据表

启动应用会自动初始化以下表：

- `milk_records`：喝奶记录（`record_time`, `milk_ml`）
- `poop_records`：拉臭臭记录（`record_time`, `poop_status`）
- `album_photos`：相册图片（`image_path`, `created_at`）

并设置 SQLite 参数：

- `PRAGMA journal_mode=WAL;`
- `PRAGMA synchronous=NORMAL;`
- `PRAGMA foreign_keys=ON;`

## 项目结构（核心）

- `app.py`：路由、数据库、看板统计、相册上传删除
- `config.py`：轻量配置
- `templates/index.html`：首页大屏
- `templates/quick.html`：快捷录入入口
- `templates/milk.html`：喝奶录入页
- `templates/poop.html`：拉臭臭录入页
- `templates/album.html`：相册页
- `static/css/main.css`：整体温馨移动端样式
- `static/js/album-vue.js`：相册页 Vue 交互
