# 语沁成长记录（轻量版）

一个轻量级 Web + H5 工程，用于记录女儿语沁的成长信息：

- 身高 / 体重 / 头围
- 成长照片上传
- 首页大屏统计（趋势图 + 核心指标）
- 成长轨迹时间线
- 手机端（H5）录入

## 技术栈

- Python + Flask（轻量）
- SQLite（单文件数据库，资源占用低）
- 原生 HTML/CSS + Chart.js

## 启动（本地）

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

启动后访问：

- 首页：<http://127.0.0.1:8000/>
- H5 提交：<http://127.0.0.1:8000/submit>

## 自动部署到服务器（已支持）

项目包含 Docker + GitHub Actions 自动部署方案：

- `Dockerfile` + `docker-compose.yml`：容器化运行应用
- `.github/workflows/deploy.yml`：当 `main` 分支有新提交时，自动 SSH 到服务器执行部署
- `scripts/deploy.sh`：服务器端拉取最新代码并重启容器

### 服务器首次准备

```bash
# 以 Ubuntu 为例
sudo apt update
sudo apt install -y git docker.io docker-compose-plugin
sudo usermod -aG docker $USER

# 预创建目录
sudo mkdir -p /opt/yqlog
sudo chown -R $USER:$USER /opt/yqlog
```

### GitHub Secrets 配置

在仓库 `Settings -> Secrets and variables -> Actions` 新增：

- `DEPLOY_HOST`: 服务器公网 IP 或域名
- `DEPLOY_USER`: SSH 用户（例如 `ubuntu`）
- `DEPLOY_SSH_KEY`: 私钥内容（与服务器公钥配对）
- `DEPLOY_APP_DIR`: 部署目录（例如 `/opt/yqlog`）
- `FLASK_SECRET_KEY`: Flask 生产环境密钥

> 提示：首次部署时，建议先在服务器手动 `git clone` 到 `DEPLOY_APP_DIR`，确保目录结构和权限正确。

## 目录说明

- `app.py`: 主程序（路由、数据库、上传处理）
- `templates/`: 页面模板
- `static/css/main.css`: 样式
- `static/js/main.js`: 前端交互增强（上传预览、提交中状态）
- `.github/workflows/deploy.yml`: 自动部署工作流
- `scripts/deploy.sh`: 服务器部署脚本
- `data/yqlog.db`: SQLite 数据库（运行后自动创建）
- `uploads/`: 图片上传目录

## 后续建议

- 增加登录鉴权（保护隐私）
- 增加导出功能（CSV / ZIP）
- 增加定时备份 SQLite 文件
