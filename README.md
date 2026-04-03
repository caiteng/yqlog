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

## 启动

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

启动后访问：

- 首页：<http://127.0.0.1:8000/>
- H5 提交：<http://127.0.0.1:8000/submit>

## 目录说明

- `app.py`: 主程序（路由、数据库、上传处理）
- `templates/`: 页面模板
- `static/css/main.css`: 样式
- `data/yqlog.db`: SQLite 数据库（运行后自动创建）
- `uploads/`: 图片上传目录

## 后续建议

- 增加登录鉴权（保护隐私）
- 增加导出功能（CSV / ZIP）
- 增加定时备份 SQLite 文件
