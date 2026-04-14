# YTL 博客系统

基于 Flask 构建的轻量级博客系统，支持 Railway 一键部署。

## 功能特性

- 文章发布、编辑、删除
- 文章分类和标签
- 用户注册/登录系统
- 文章搜索功能
- 响应式设计（支持移动端）
- 浏览量统计
- 管理员后台

## 技术栈

- **后端**: Flask + SQLAlchemy
- **数据库**: SQLite (本地) / PostgreSQL (生产环境)
- **前端**: Bootstrap 5 + Bootstrap Icons
- **部署**: Railway + Gunicorn

## 本地开发

### 1. 克隆项目

```bash
git clone https://github.com/ytlgithu/YTL-Blog-System.git
cd YTL-Blog-System
```

### 2. 创建虚拟环境

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 运行应用

```bash
python app.py
```

访问 http://localhost:5000

### 5. 默认管理员账户

- 用户名: `admin`
- 密码: `admin123`

> 建议登录后立即修改密码

## Railway 部署

### 1. 准备

确保代码已推送到 GitHub

### 2. 部署步骤

1. 访问 [Railway](https://railway.app) 并登录
2. 点击 "New Project" → "Deploy from GitHub repo"
3. 选择 `YTL-Blog-System` 仓库
4. Railway 会自动检测并部署
5. 部署完成后，点击 "Settings" → "Domains" 查看访问链接

### 3. 环境变量配置

在 Railway 项目设置中添加：

```
SECRET_KEY=your-secret-key-here
DATABASE_URL=${{Postgres.DATABASE_URL}}  # 自动添加
```

### 4. 数据库

Railway 会自动提供 PostgreSQL 数据库，无需手动配置。

## 项目结构

```
YTL-Blog-System/
├── app.py              # 主应用文件
├── requirements.txt    # Python 依赖
├── Procfile           # Railway 启动命令
├── railway.json       # Railway 配置
├── runtime.txt        # Python 版本
├── templates/         # HTML 模板
│   ├── base.html
│   ├── index.html
│   ├── post_detail.html
│   ├── post_edit.html
│   ├── post_list.html
│   ├── login.html
│   ├── register.html
│   └── user_list.html
└── static/            # 静态文件
    ├── css/
    └── js/
```

## 使用说明

### 写文章

1. 登录账号
2. 点击导航栏 "写文章"
3. 填写标题、分类、内容
4. 点击 "发布文章"

### 文章管理

- 编辑：在文章详情页点击 "编辑" 按钮
- 删除：在文章详情页点击 "删除" 按钮

### 搜索

在导航栏搜索框输入关键词，支持按标题和内容搜索。

## 许可证

MIT License
