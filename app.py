import os
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# 创建应用
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///blog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 东八区时间
CN_TIMEZONE = timezone(timedelta(hours=8))

def cn_now():
    return datetime.now(CN_TIMEZONE)

# 用户模型
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=cn_now)
    
    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 文章模型
class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(500))
    category = db.Column(db.String(50), default='技术')
    tags = db.Column(db.String(200))
    is_published = db.Column(db.Boolean, default=True)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=cn_now, index=True)
    updated_at = db.Column(db.DateTime, default=cn_now, onupdate=cn_now)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('权限不足', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# 首页
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    query = Post.query.filter_by(is_published=True)
    
    if category:
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(
            db.or_(
                Post.title.contains(search),
                Post.content.contains(search)
            )
        )
    
    posts = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    categories = db.session.query(Post.category).distinct().all()
    categories = [c[0] for c in categories]
    
    return render_template('index.html', posts=posts, categories=categories, 
                         current_category=category, search=search)

# 文章详情
@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    if not post.is_published:
        abort(404)
    
    # 增加浏览量
    post.view_count += 1
    db.session.commit()
    
    # 相关文章
    related_posts = Post.query.filter(
        Post.category == post.category,
        Post.id != post.id,
        Post.is_published == True
    ).order_by(Post.created_at.desc()).limit(5).all()
    
    return render_template('post_detail.html', post=post, related_posts=related_posts)

# 文章列表
@app.route('/posts')
def post_list():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(is_published=True).order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=12, error_out=False)
    return render_template('post_list.html', posts=posts)

# 新建文章
@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def post_new():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        summary = request.form.get('summary', '').strip()
        category = request.form.get('category', '技术').strip()
        tags = request.form.get('tags', '').strip()
        is_published = request.form.get('is_published') == 'on'
        
        if not title or not content:
            flash('标题和内容不能为空', 'danger')
            return redirect(url_for('post_new'))
        
        post = Post(
            title=title,
            content=content,
            summary=summary or content[:200] + '...',
            category=category,
            tags=tags,
            is_published=is_published,
            user_id=session['user_id']
        )
        db.session.add(post)
        db.session.commit()
        flash('文章发布成功', 'success')
        return redirect(url_for('post_detail', post_id=post.id))
    
    categories = db.session.query(Post.category).distinct().all()
    categories = [c[0] for c in categories]
    return render_template('post_edit.html', categories=categories)

# 编辑文章
@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def post_edit(post_id):
    post = Post.query.get_or_404(post_id)
    
    # 检查权限
    if post.user_id != session['user_id'] and not session.get('is_admin'):
        flash('无权编辑此文章', 'danger')
        return redirect(url_for('post_detail', post_id=post.id))
    
    if request.method == 'POST':
        post.title = request.form.get('title', '').strip()
        post.content = request.form.get('content', '').strip()
        post.summary = request.form.get('summary', '').strip()
        post.category = request.form.get('category', '技术').strip()
        post.tags = request.form.get('tags', '').strip()
        post.is_published = request.form.get('is_published') == 'on'
        
        if not post.title or not post.content:
            flash('标题和内容不能为空', 'danger')
            return redirect(url_for('post_edit', post_id=post.id))
        
        db.session.commit()
        flash('文章更新成功', 'success')
        return redirect(url_for('post_detail', post_id=post.id))
    
    categories = db.session.query(Post.category).distinct().all()
    categories = [c[0] for c in categories]
    return render_template('post_edit.html', post=post, categories=categories)

# 删除文章
@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def post_delete(post_id):
    post = Post.query.get_or_404(post_id)
    
    # 检查权限
    if post.user_id != session['user_id'] and not session.get('is_admin'):
        flash('无权删除此文章', 'danger')
        return redirect(url_for('post_detail', post_id=post.id))
    
    db.session.delete(post)
    db.session.commit()
    flash('文章已删除', 'success')
    return redirect(url_for('index'))

# 用户注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not username or not email or not password:
            flash('请填写所有字段', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# 用户登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash(f'欢迎回来，{user.username}！', 'success')
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误', 'danger')
    
    return render_template('login.html')

# 用户登出
@app.route('/logout')
def logout():
    session.clear()
    flash('已退出登录', 'info')
    return redirect(url_for('index'))

# 用户列表（管理员）
@app.route('/admin/users')
@admin_required
def user_list():
    users = User.query.all()
    return render_template('user_list.html', users=users)

# 初始化数据库命令
@app.cli.command('init-db')
def init_db_command():
    db.create_all()
    
    # 创建默认管理员账户
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('数据库初始化完成！')
        print('默认管理员账户：admin / admin123')
    else:
        print('数据库已存在')

# 创建数据库表和管理员账户（在应用上下文中）
with app.app_context():
    db.create_all()
    
    # 自动创建默认管理员账户
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('[INIT] 默认管理员账户创建成功: admin / admin123')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
