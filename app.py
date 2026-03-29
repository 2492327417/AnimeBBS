"""
次元漫谈 - 动漫交流论坛
主应用文件
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'animebbs_secret_key_2024_secure'

# 数据库路径
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'animebbs.db')


# ==================== 数据库工具函数 ====================

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
    return conn


def init_db():
    """初始化数据库，创建表结构并插入初始数据"""
    conn = get_db()
    cursor = conn.cursor()

    # 读取并执行schema.sql
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        cursor.executescript(f.read())

    # 检查管理员是否存在，不存在则创建
    admin = cursor.execute('SELECT id FROM users WHERE username = ?', ('admin',)).fetchone()
    if not admin:
        admin_password = generate_password_hash('admin123')
        cursor.execute(
            'INSERT INTO users (username, password_hash, is_admin, bio) VALUES (?, ?, ?, ?)',
            ('admin', admin_password, 1, '论坛管理员，维护次元漫谈的秩序与和谐。')
        )

    # 检查默认分类是否存在
    categories = cursor.execute('SELECT COUNT(*) FROM categories').fetchone()[0]
    if categories == 0:
        default_categories = [
            ('新番讨论', '讨论最新动漫番剧', '🎬'),
            ('漫画推荐', '分享和推荐优质漫画作品', '📚'),
            ('声优杂谈', '关于配音演员的一切', '🎙️'),
            ('游戏同好', '动漫改编游戏及相关讨论', '🎮'),
            ('手办周边', '展示和讨论手办、周边收藏', '🗿'),
            ('同人创作', '分享同人绘画、写作等创作', '✏️'),
        ]
        cursor.executemany(
            'INSERT INTO categories (name, description, icon) VALUES (?, ?, ?)',
            default_categories
        )

    conn.commit()
    conn.close()
    print("[OK] 数据库初始化完成！")


# ==================== 装饰器 ====================

def login_required(f):
    """需要登录的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录后再进行此操作', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """需要管理员权限的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            flash('此页面仅管理员可访问', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== 上下文处理器 ====================

@app.context_processor
def inject_user():
    """向所有模板注入当前用户信息"""
    user = None
    if 'user_id' in session:
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
    return {'current_user': user}


@app.context_processor
def inject_categories():
    """向所有模板注入分类列表"""
    conn = get_db()
    categories = conn.execute('SELECT * FROM categories ORDER BY id').fetchall()
    conn.close()
    return {'all_categories': categories}


# ==================== 首页路由 ====================

@app.route('/')
def index():
    """首页 - 展示所有帖子"""
    page = request.args.get('page', 1, type=int)
    per_page = 15
    category_id = request.args.get('category', None, type=int)
    search_query = request.args.get('q', '').strip()

    conn = get_db()

    # 构建查询
    base_query = '''
        SELECT p.*, u.username, u.avatar, c.name as category_name, c.icon as category_icon,
               (SELECT COUNT(*) FROM replies r WHERE r.post_id = p.id) as reply_count
        FROM posts p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.is_deleted = 0
    '''
    params = []

    if category_id:
        base_query += ' AND p.category_id = ?'
        params.append(category_id)

    if search_query:
        base_query += ' AND (p.title LIKE ? OR p.content LIKE ?)'
        params.extend([f'%{search_query}%', f'%{search_query}%'])

    # 统计总数
    count_query = f'SELECT COUNT(*) FROM ({base_query})'
    total = conn.execute(count_query, params).fetchone()[0]

    # 分页查询
    base_query += ' ORDER BY p.created_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, (page - 1) * per_page])
    posts = conn.execute(base_query, params).fetchall()

    # 统计信息
    total_posts = conn.execute('SELECT COUNT(*) FROM posts WHERE is_deleted = 0').fetchone()[0]
    total_users = conn.execute('SELECT COUNT(*) FROM users WHERE is_banned = 0').fetchone()[0]
    total_replies = conn.execute('SELECT COUNT(*) FROM replies').fetchone()[0]

    # 热门帖子（回复最多）
    hot_posts = conn.execute('''
        SELECT p.id, p.title, u.username,
               (SELECT COUNT(*) FROM replies r WHERE r.post_id = p.id) as reply_count
        FROM posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.is_deleted = 0
        ORDER BY reply_count DESC
        LIMIT 5
    ''').fetchall()

    conn.close()

    total_pages = (total + per_page - 1) // per_page
    current_category = category_id

    return render_template('index.html',
                           posts=posts,
                           page=page,
                           total_pages=total_pages,
                           total=total,
                           current_category=current_category,
                           search_query=search_query,
                           total_posts=total_posts,
                           total_users=total_users,
                           total_replies=total_replies,
                           hot_posts=hot_posts)


# ==================== 认证路由 ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # 验证输入
        if not username or not password:
            flash('用户名和密码不能为空', 'danger')
            return render_template('register.html')

        if len(username) < 2 or len(username) > 20:
            flash('用户名长度需在2-20个字符之间', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('密码长度不能少于6个字符', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return render_template('register.html')

        conn = get_db()
        # 检查用户名是否已存在
        existing = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            flash('该用户名已被注册，请换一个', 'danger')
            conn.close()
            return render_template('register.html')

        # 创建用户
        password_hash = generate_password_hash(password)
        cursor = conn.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        # 自动登录
        session['user_id'] = user_id
        session['username'] = username
        session['is_admin'] = False

        flash(f'欢迎加入次元漫谈，{username}！', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('请输入用户名和密码', 'danger')
            return render_template('login.html')

        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if not user or not check_password_hash(user['password_hash'], password):
            flash('用户名或密码错误', 'danger')
            return render_template('login.html')

        if user['is_banned']:
            flash('您的账号已被封禁，如有疑问请联系管理员', 'danger')
            return render_template('login.html')

        # 设置session
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['is_admin'] = bool(user['is_admin'])

        flash(f'欢迎回来，{username}！', 'success')
        next_url = request.args.get('next')
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    """退出登录"""
    username = session.get('username', '')
    session.clear()
    flash(f'再见，{username}！期待下次与您相遇~', 'info')
    return redirect(url_for('index'))


# ==================== 帖子路由 ====================

@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    """发布新帖子"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category_id = request.form.get('category_id', type=int)

        if not title or not content:
            flash('标题和内容不能为空', 'danger')
            return redirect(url_for('new_post'))

        if len(title) > 100:
            flash('标题不能超过100个字符', 'danger')
            return redirect(url_for('new_post'))

        conn = get_db()
        # 检查用户是否被封禁
        user = conn.execute('SELECT is_banned FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        if user['is_banned']:
            flash('您的账号已被封禁，无法发帖', 'danger')
            conn.close()
            return redirect(url_for('index'))

        cursor = conn.execute(
            'INSERT INTO posts (user_id, category_id, title, content) VALUES (?, ?, ?, ?)',
            (session['user_id'], category_id, title, content)
        )
        conn.commit()
        post_id = cursor.lastrowid
        conn.close()

        flash('帖子发布成功！', 'success')
        return redirect(url_for('post_detail', post_id=post_id))

    return render_template('new_post.html')


@app.route('/post/<int:post_id>')
def post_detail(post_id):
    """帖子详情页"""
    conn = get_db()
    post = conn.execute('''
        SELECT p.*, u.username, u.avatar, u.bio, c.name as category_name, c.icon as category_icon
        FROM posts p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.id = ? AND p.is_deleted = 0
    ''', (post_id,)).fetchone()

    if not post:
        conn.close()
        flash('帖子不存在或已被删除', 'warning')
        return redirect(url_for('index'))

    # 增加浏览次数
    conn.execute('UPDATE posts SET view_count = view_count + 1 WHERE id = ?', (post_id,))
    conn.commit()

    # 获取回复
    replies = conn.execute('''
        SELECT r.*, u.username, u.avatar
        FROM replies r
        JOIN users u ON r.user_id = u.id
        WHERE r.post_id = ?
        ORDER BY r.created_at ASC
    ''', (post_id,)).fetchall()

    conn.close()
    return render_template('post_detail.html', post=post, replies=replies)


@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    """编辑帖子"""
    conn = get_db()
    post = conn.execute('SELECT * FROM posts WHERE id = ? AND is_deleted = 0', (post_id,)).fetchone()

    if not post:
        conn.close()
        flash('帖子不存在', 'warning')
        return redirect(url_for('index'))

    # 只有作者可以编辑
    if post['user_id'] != session['user_id'] and not session.get('is_admin'):
        conn.close()
        flash('您没有权限编辑此帖子', 'danger')
        return redirect(url_for('post_detail', post_id=post_id))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category_id = request.form.get('category_id', type=int)

        if not title or not content:
            flash('标题和内容不能为空', 'danger')
            return render_template('edit_post.html', post=post)

        conn.execute(
            'UPDATE posts SET title = ?, content = ?, category_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (title, content, category_id, post_id)
        )
        conn.commit()
        conn.close()

        flash('帖子已更新', 'success')
        return redirect(url_for('post_detail', post_id=post_id))

    conn.close()
    return render_template('edit_post.html', post=post)


@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    """删除帖子（软删除）"""
    conn = get_db()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()

    if not post:
        conn.close()
        flash('帖子不存在', 'warning')
        return redirect(url_for('index'))

    if post['user_id'] != session['user_id'] and not session.get('is_admin'):
        conn.close()
        flash('您没有权限删除此帖子', 'danger')
        return redirect(url_for('post_detail', post_id=post_id))

    conn.execute('UPDATE posts SET is_deleted = 1 WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()

    flash('帖子已删除', 'success')
    return redirect(url_for('index'))


# ==================== 回复路由 ====================

@app.route('/post/<int:post_id>/reply', methods=['POST'])
@login_required
def add_reply(post_id):
    """发布回复"""
    content = request.form.get('content', '').strip()

    if not content:
        flash('回复内容不能为空', 'danger')
        return redirect(url_for('post_detail', post_id=post_id))

    conn = get_db()

    # 检查用户是否被封禁
    user = conn.execute('SELECT is_banned FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    if user['is_banned']:
        flash('您的账号已被封禁，无法回复', 'danger')
        conn.close()
        return redirect(url_for('post_detail', post_id=post_id))

    # 检查帖子是否存在
    post = conn.execute('SELECT id FROM posts WHERE id = ? AND is_deleted = 0', (post_id,)).fetchone()
    if not post:
        flash('帖子不存在', 'warning')
        conn.close()
        return redirect(url_for('index'))

    conn.execute(
        'INSERT INTO replies (post_id, user_id, content) VALUES (?, ?, ?)',
        (post_id, session['user_id'], content)
    )
    conn.commit()
    conn.close()

    flash('回复成功！', 'success')
    return redirect(url_for('post_detail', post_id=post_id) + '#replies')


@app.route('/reply/<int:reply_id>/delete', methods=['POST'])
@login_required
def delete_reply(reply_id):
    """删除回复"""
    conn = get_db()
    reply = conn.execute('SELECT * FROM replies WHERE id = ?', (reply_id,)).fetchone()

    if not reply:
        conn.close()
        flash('回复不存在', 'warning')
        return redirect(url_for('index'))

    if reply['user_id'] != session['user_id'] and not session.get('is_admin'):
        conn.close()
        flash('您没有权限删除此回复', 'danger')
        return redirect(url_for('post_detail', post_id=reply['post_id']))

    post_id = reply['post_id']
    conn.execute('DELETE FROM replies WHERE id = ?', (reply_id,))
    conn.commit()
    conn.close()

    flash('回复已删除', 'success')
    return redirect(url_for('post_detail', post_id=post_id))


# ==================== 用户页面路由 ====================

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    """查看用户主页"""
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if not user:
        conn.close()
        flash('用户不存在', 'warning')
        return redirect(url_for('index'))

    # 获取用户帖子
    posts = conn.execute('''
        SELECT p.*, c.name as category_name, c.icon as category_icon,
               (SELECT COUNT(*) FROM replies r WHERE r.post_id = p.id) as reply_count
        FROM posts p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.user_id = ? AND p.is_deleted = 0
        ORDER BY p.created_at DESC
    ''', (user_id,)).fetchall()

    post_count = len(posts)
    reply_count = conn.execute('SELECT COUNT(*) FROM replies WHERE user_id = ?', (user_id,)).fetchone()[0]

    conn.close()
    return render_template('user_profile.html', profile_user=user, posts=posts,
                           post_count=post_count, reply_count=reply_count)


@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """编辑个人资料"""
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    if request.method == 'POST':
        bio = request.form.get('bio', '').strip()
        avatar = request.form.get('avatar', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if len(bio) > 200:
            flash('个人简介不能超过200个字符', 'danger')
            return render_template('edit_profile.html', user=user)

        update_data = {'bio': bio, 'avatar': avatar}

        # 修改密码
        if new_password:
            if len(new_password) < 6:
                flash('新密码长度不能少于6个字符', 'danger')
                return render_template('edit_profile.html', user=user)
            if new_password != confirm_password:
                flash('两次输入的密码不一致', 'danger')
                return render_template('edit_profile.html', user=user)
            update_data['password_hash'] = generate_password_hash(new_password)

        if new_password:
            conn.execute(
                'UPDATE users SET bio = ?, avatar = ?, password_hash = ? WHERE id = ?',
                (bio, avatar, update_data['password_hash'], session['user_id'])
            )
        else:
            conn.execute(
                'UPDATE users SET bio = ?, avatar = ? WHERE id = ?',
                (bio, avatar, session['user_id'])
            )

        conn.commit()
        conn.close()
        flash('个人资料已更新', 'success')
        return redirect(url_for('user_profile', user_id=session['user_id']))

    conn.close()
    return render_template('edit_profile.html', user=user)


@app.route('/my/posts')
@login_required
def my_posts():
    """我的帖子"""
    conn = get_db()
    posts = conn.execute('''
        SELECT p.*, c.name as category_name, c.icon as category_icon,
               (SELECT COUNT(*) FROM replies r WHERE r.post_id = p.id) as reply_count
        FROM posts p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.user_id = ? AND p.is_deleted = 0
        ORDER BY p.created_at DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('my_posts.html', posts=posts)


# ==================== 管理员路由 ====================

@app.route('/admin')
@admin_required
def admin_index():
    """管理员首页"""
    conn = get_db()
    stats = {
        'total_users': conn.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        'total_posts': conn.execute('SELECT COUNT(*) FROM posts WHERE is_deleted = 0').fetchone()[0],
        'total_replies': conn.execute('SELECT COUNT(*) FROM replies').fetchone()[0],
        'banned_users': conn.execute('SELECT COUNT(*) FROM users WHERE is_banned = 1').fetchone()[0],
        'total_categories': conn.execute('SELECT COUNT(*) FROM categories').fetchone()[0],
    }

    # 最近帖子
    recent_posts = conn.execute('''
        SELECT p.*, u.username
        FROM posts p JOIN users u ON p.user_id = u.id
        WHERE p.is_deleted = 0
        ORDER BY p.created_at DESC LIMIT 10
    ''').fetchall()

    # 最近注册用户
    recent_users = conn.execute('''
        SELECT * FROM users ORDER BY created_at DESC LIMIT 10
    ''').fetchall()

    conn.close()
    return render_template('admin/index.html', stats=stats,
                           recent_posts=recent_posts, recent_users=recent_users)


@app.route('/admin/users')
@admin_required
def admin_users():
    """管理员 - 用户管理"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('q', '').strip()

    conn = get_db()
    if search:
        users = conn.execute('''
            SELECT u.*, 
                   (SELECT COUNT(*) FROM posts p WHERE p.user_id = u.id AND p.is_deleted = 0) as post_count
            FROM users u
            WHERE u.username LIKE ?
            ORDER BY u.created_at DESC
            LIMIT ? OFFSET ?
        ''', (f'%{search}%', per_page, (page - 1) * per_page)).fetchall()
        total = conn.execute('SELECT COUNT(*) FROM users WHERE username LIKE ?',
                             (f'%{search}%',)).fetchone()[0]
    else:
        users = conn.execute('''
            SELECT u.*, 
                   (SELECT COUNT(*) FROM posts p WHERE p.user_id = u.id AND p.is_deleted = 0) as post_count
            FROM users u
            ORDER BY u.created_at DESC
            LIMIT ? OFFSET ?
        ''', (per_page, (page - 1) * per_page)).fetchall()
        total = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]

    conn.close()
    total_pages = (total + per_page - 1) // per_page
    return render_template('admin/users.html', users=users, page=page,
                           total_pages=total_pages, search=search)


@app.route('/admin/users/<int:user_id>/toggle_ban', methods=['POST'])
@admin_required
def toggle_ban(user_id):
    """封禁/解封用户"""
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if not user:
        conn.close()
        flash('用户不存在', 'warning')
        return redirect(url_for('admin_users'))

    if user['is_admin']:
        conn.close()
        flash('不能封禁管理员账号', 'danger')
        return redirect(url_for('admin_users'))

    new_status = 0 if user['is_banned'] else 1
    conn.execute('UPDATE users SET is_banned = ? WHERE id = ?', (new_status, user_id))
    conn.commit()
    conn.close()

    action = '封禁' if new_status else '解封'
    flash(f'已{action}用户 {user["username"]}', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/posts')
@admin_required
def admin_posts():
    """管理员 - 帖子管理"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    conn = get_db()
    posts = conn.execute('''
        SELECT p.*, u.username, c.name as category_name
        FROM posts p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.created_at DESC
        LIMIT ? OFFSET ?
    ''', (per_page, (page - 1) * per_page)).fetchall()

    total = conn.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
    conn.close()

    total_pages = (total + per_page - 1) // per_page
    return render_template('admin/posts.html', posts=posts, page=page, total_pages=total_pages)


@app.route('/admin/posts/<int:post_id>/delete', methods=['POST'])
@admin_required
def admin_delete_post(post_id):
    """管理员删除帖子"""
    conn = get_db()
    conn.execute('UPDATE posts SET is_deleted = 1 WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    flash('帖子已删除', 'success')
    return redirect(url_for('admin_posts'))


@app.route('/admin/posts/<int:post_id>/restore', methods=['POST'])
@admin_required
def admin_restore_post(post_id):
    """管理员恢复帖子"""
    conn = get_db()
    conn.execute('UPDATE posts SET is_deleted = 0 WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    flash('帖子已恢复', 'success')
    return redirect(url_for('admin_posts'))


@app.route('/admin/categories')
@admin_required
def admin_categories():
    """管理员 - 分类管理"""
    conn = get_db()
    categories = conn.execute('''
        SELECT c.*, COUNT(p.id) as post_count
        FROM categories c
        LEFT JOIN posts p ON p.category_id = c.id AND p.is_deleted = 0
        GROUP BY c.id
        ORDER BY c.id
    ''').fetchall()
    conn.close()
    return render_template('admin/categories.html', categories=categories)


@app.route('/admin/categories/add', methods=['POST'])
@admin_required
def add_category():
    """添加分类"""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    icon = request.form.get('icon', '📌').strip()

    if not name:
        flash('分类名称不能为空', 'danger')
        return redirect(url_for('admin_categories'))

    conn = get_db()
    existing = conn.execute('SELECT id FROM categories WHERE name = ?', (name,)).fetchone()
    if existing:
        flash('该分类名称已存在', 'danger')
        conn.close()
        return redirect(url_for('admin_categories'))

    conn.execute('INSERT INTO categories (name, description, icon) VALUES (?, ?, ?)',
                 (name, description, icon))
    conn.commit()
    conn.close()
    flash(f'分类"{name}"已添加', 'success')
    return redirect(url_for('admin_categories'))


@app.route('/admin/categories/<int:cat_id>/edit', methods=['POST'])
@admin_required
def edit_category(cat_id):
    """编辑分类"""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    icon = request.form.get('icon', '📌').strip()

    if not name:
        flash('分类名称不能为空', 'danger')
        return redirect(url_for('admin_categories'))

    conn = get_db()
    conn.execute('UPDATE categories SET name = ?, description = ?, icon = ? WHERE id = ?',
                 (name, description, icon, cat_id))
    conn.commit()
    conn.close()
    flash('分类已更新', 'success')
    return redirect(url_for('admin_categories'))


@app.route('/admin/categories/<int:cat_id>/delete', methods=['POST'])
@admin_required
def delete_category(cat_id):
    """删除分类"""
    conn = get_db()
    # 将该分类下的帖子设为未分类
    conn.execute('UPDATE posts SET category_id = NULL WHERE category_id = ?', (cat_id,))
    conn.execute('DELETE FROM categories WHERE id = ?', (cat_id,))
    conn.commit()
    conn.close()
    flash('分类已删除', 'success')
    return redirect(url_for('admin_categories'))


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404, message='页面不存在'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', code=500, message='服务器内部错误'), 500


# ==================== 主程序入口 ====================

if __name__ == '__main__':
    # 检查数据库是否存在，不存在则初始化
    if not os.path.exists(DATABASE):
        print("[INIT] First run, initializing database...")
        init_db()
    else:
        print("[OK] Database exists, skipping init")
    
    print("[START] AnimeBBS starting...")
    print("[URL]   http://127.0.0.1:5000")
    print("[ADMIN] admin / admin123")
    app.run(debug=True, host='0.0.0.0', port=5000)
