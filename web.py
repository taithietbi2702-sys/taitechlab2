from flask import Flask, render_template, url_for, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
import re
import markdown as md
from datetime import datetime

app = Flask(__name__)
db_url = os.environ.get('DATABASE_URL')
if db_url:
	# Render / some providers may provide DATABASE_URL with postgres:// prefix
	if db_url.startswith('postgres://'):
		db_url = db_url.replace('postgres://', 'postgresql://', 1)
	app.config['SQLALCHEMY_DATABASE_URI'] = db_url
else:
	app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret')

db = SQLAlchemy(app)


class Post(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(200), nullable=False)
	slug = db.Column(db.String(200), unique=True, nullable=False)
	content = db.Column(db.Text, nullable=False)
	created = db.Column(db.DateTime, default=datetime.utcnow)


def make_slug(title: str) -> str:
	slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title)
	slug = re.sub(r'\s+', '-', slug).strip('-').lower()
	# ensure uniqueness
	base = slug
	i = 1
	while Post.query.filter_by(slug=slug).first():
		slug = f"{base}-{i}"
		i += 1
	return slug


@app.before_first_request
def ensure_db():
	db.create_all()


@app.route('/')
def index():
	posts = Post.query.order_by(Post.created.desc()).limit(10).all()
	return render_template('index.html', posts=posts)


@app.route('/posts/<slug>')
def show_post(slug):
	post = Post.query.filter_by(slug=slug).first_or_404()
	html = md.markdown(post.content or '', extensions=['fenced_code', 'tables'])
	return render_template('post.html', post=post, html=html)


@app.route('/dien-cong-nghiep')
def dien_cong_nghiep():
	return render_template('electric.html')


@app.route('/co-khi')
def co_khi():
	return render_template('mechanical.html')


@app.route('/robot')
def robot():
	return render_template('robot.html')


@app.route('/phan-mem')
def phan_mem():
	return render_template('software.html')


# --- Simple admin (session + env password) ---
def is_admin() -> bool:
	return session.get('admin', False)


def admin_required(fn):
	from functools import wraps

	@wraps(fn)
	def wrapper(*a, **kw):
		if not is_admin():
			return redirect(url_for('admin_login'))
		return fn(*a, **kw)

	return wrapper


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
	if request.method == 'POST':
		pw = request.form.get('password', '')
		if pw and pw == os.environ.get('ADMIN_PASSWORD', 'admin'):
			session['admin'] = True
			flash('Đã đăng nhập', 'success')
			return redirect(url_for('admin_index'))
		flash('Mật khẩu sai', 'error')
	return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
	session.pop('admin', None)
	return redirect(url_for('index'))


@app.route('/admin')
@admin_required
def admin_index():
	posts = Post.query.order_by(Post.created.desc()).all()
	return render_template('admin/list.html', posts=posts)


@app.route('/admin/new', methods=['GET', 'POST'])
@admin_required
def admin_new():
	if request.method == 'POST':
		title = request.form.get('title', '').strip()
		content = request.form.get('content', '').strip()
		if not title:
			flash('Title required', 'error')
		else:
			slug = make_slug(title)
			post = Post(title=title, slug=slug, content=content)
			db.session.add(post)
			db.session.commit()
			return redirect(url_for('admin_index'))
	return render_template('admin/edit.html', post=None)


@app.route('/admin/edit/<int:post_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit(post_id):
	post = Post.query.get_or_404(post_id)
	if request.method == 'POST':
		post.title = request.form.get('title', post.title).strip()
		post.content = request.form.get('content', post.content)
		db.session.commit()
		return redirect(url_for('admin_index'))
	return render_template('admin/edit.html', post=post)


@app.route('/admin/delete/<int:post_id>', methods=['POST'])
@admin_required
def admin_delete(post_id):
	post = Post.query.get_or_404(post_id)
	db.session.delete(post)
	db.session.commit()
	return redirect(url_for('admin_index'))


if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=5000)
