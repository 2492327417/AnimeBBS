# 🌸 次元漫谈 - 动漫交流论坛

> 一个基于 Flask + SQLite 构建的动漫主题社区论坛，清新动漫风格，功能完整，适合本地部署。

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-2.3+-green)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightblue)

---

## ✨ 功能特性

### 🏠 首页
- 帖子列表按时间倒序排列，支持分类筛选与关键词搜索
- 展示帖子标题、作者、分类、发布时间及回复数
- 响应式布局，侧边栏显示热门帖子、分类导航、论坛统计

### 👤 用户功能
- 注册 / 登录 / 退出（密码 bcrypt 加密存储）
- 个人主页：查看个人信息、历史帖子
- 编辑资料：修改个人简介、头像 URL、密码
- 发帖 / 编辑 / 删除自己的帖子
- 在帖子下发表回复，支持删除自己的回复

### ⚙️ 管理员功能（`admin` / `admin123`）
- 控制台：统计用户数、帖子数、回复数等
- 用户管理：查看所有用户，一键封禁 / 解封
- 帖子管理：查看所有帖子，删除违规内容，支持恢复
- 分类管理：新增、编辑、删除帖子分类

---

## 📁 项目结构

```
AnimeBBS/
├── app.py              # Flask 主应用（路由 + 业务逻辑）
├── schema.sql          # 数据库建表脚本
├── requirements.txt    # Python 依赖
├── animebbs.db         # SQLite 数据库（运行后自动生成）
├── static/
│   ├── css/
│   │   └── style.css   # 主样式（动漫暗色主题）
│   └── js/
│       └── main.js     # 前端交互脚本
└── templates/
    ├── base.html        # 基础模板（导航栏 + Footer）
    ├── index.html       # 首页
    ├── post_detail.html # 帖子详情 + 回复
    ├── new_post.html    # 发帖页
    ├── edit_post.html   # 编辑帖子
    ├── user_profile.html# 用户主页
    ├── edit_profile.html# 编辑资料
    ├── my_posts.html    # 我的帖子
    ├── login.html       # 登录
    ├── register.html    # 注册
    ├── error.html       # 错误页
    └── admin/
        ├── index.html   # 管理控制台
        ├── users.html   # 用户管理
        ├── posts.html   # 帖子管理
        └── categories.html # 分类管理
```

---

## 🚀 快速开始

### 1. 环境要求
- Python 3.8 或更高版本
- pip（Python 包管理器）

### 2. 克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/AnimeBBS.git
cd AnimeBBS
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

> 💡 推荐使用虚拟环境：
> ```bash
> python -m venv venv
> # Windows
> venv\Scripts\activate
> # macOS/Linux
> source venv/bin/activate
> pip install -r requirements.txt
> ```

### 4. 运行项目

```bash
python app.py
```

首次运行时会自动：
- 创建 SQLite 数据库 `animebbs.db`
- 执行 `schema.sql` 创建所有数据表
- 创建管理员账号和默认分类

### 5. 访问论坛

打开浏览器访问：**http://127.0.0.1:5000**

---

## 🔑 默认账号

| 账号 | 密码 | 权限 |
|------|------|------|
| `admin` | `admin123` | 管理员 |

> ⚠️ 生产环境请务必修改管理员密码！

---

## 📂 默认版块

| 版块 | 描述 |
|------|------|
| 🎬 新番讨论 | 讨论最新动漫番剧 |
| 📚 漫画推荐 | 分享和推荐优质漫画作品 |
| 🎙️ 声优杂谈 | 关于配音演员的一切 |
| 🎮 游戏同好 | 动漫改编游戏及相关讨论 |
| 🗿 手办周边 | 展示和讨论手办、周边收藏 |
| ✏️ 同人创作 | 分享同人绘画、写作等创作 |

---

## 🛠️ 手动初始化数据库（可选）

如果需要单独初始化数据库：

```python
from app import init_db
init_db()
```

或者运行一个独立脚本：

```python
# init_db.py
from app import init_db
init_db()
```

```bash
python init_db.py
```

---

## 🎨 界面预览

- **主题色**：深空紫罗兰 + 樱花粉，动漫风暗色主题
- **响应式**：完整适配 PC 端和移动端
- **交互**：Flash 消息自动消失、删除二次确认弹窗、字数计数器

---

## 📝 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Flask 2.3+ |
| 数据库 | SQLite 3（内置，无需额外安装）|
| 密码加密 | Werkzeug `generate_password_hash` |
| 前端 | 原生 HTML5 / CSS3 / JavaScript（无框架依赖）|
| 字体 | Noto Sans SC（Google Fonts）|

---

## ⚠️ 注意事项

1. 本项目使用 `debug=True` 模式运行，**不适合直接用于生产环境**
2. 生产部署建议使用 Gunicorn + Nginx
3. 数据库文件 `animebbs.db` 已加入 `.gitignore`，不会上传到 GitHub
4. `app.secret_key` 在生产环境中应替换为随机生成的强密钥

---

## 📜 开源协议

MIT License - 自由使用、修改和分发

---

*🌸 次元漫谈 - 让每一个动漫爱好者都有地方说话*
