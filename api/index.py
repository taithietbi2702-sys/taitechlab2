import os
import re
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import markdown as md

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

# App
app = FastAPI()

# Templates and static
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Database
DATABASE_URL = os.environ.get('DATABASE_URL') or f"sqlite:///{os.path.join(BASE_DIR, 'data.db')}"
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith('sqlite') else {})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    created = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


def make_slug(title: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title)
    slug = re.sub(r'\s+', '-', slug).strip('-').lower()
    db = SessionLocal()
    base = slug
    i = 1
    while db.query(Post).filter_by(slug=slug).first():
        slug = f"{base}-{i}"
        i += 1
    db.close()
    return slug


def get_admin_from_cookie(request: Request) -> bool:
    return request.cookies.get('is_admin') == '1'


@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    db = SessionLocal()
    posts = db.query(Post).order_by(Post.created.desc()).limit(10).all()
    db.close()
    return templates.TemplateResponse('index.html', {'request': request, 'posts': posts})


@app.get('/posts/{slug}', response_class=HTMLResponse)
def show_post(request: Request, slug: str):
    db = SessionLocal()
    post = db.query(Post).filter_by(slug=slug).first()
    db.close()
    if not post:
        raise HTTPException(status_code=404, detail='Not found')
    html = md.markdown(post.content or '', extensions=['fenced_code', 'tables'])
    return templates.TemplateResponse('post.html', {'request': request, 'post': post, 'html': html})


# Admin pages
@app.get('/admin', response_class=HTMLResponse)
def admin_login_page(request: Request):
    return templates.TemplateResponse('admin/login.html', {'request': request})


@app.post('/admin/login')
def admin_login(request: Request, password: str = Form(...)):
    pw = os.environ.get('ADMIN_PASSWORD', 'admin')
    if password == pw:
        response = RedirectResponse(url='/admin/list', status_code=302)
        response.set_cookie('is_admin', '1', httponly=True)
        return response
    return templates.TemplateResponse('admin/login.html', {'request': request, 'error': 'Mật khẩu sai'})


@app.get('/admin/list', response_class=HTMLResponse)
def admin_list(request: Request):
    if not get_admin_from_cookie(request):
        return RedirectResponse(url='/admin')
    db = SessionLocal()
    posts = db.query(Post).order_by(Post.created.desc()).all()
    db.close()
    return templates.TemplateResponse('admin/list.html', {'request': request, 'posts': posts})


@app.get('/admin/new', response_class=HTMLResponse)
def admin_new_page(request: Request):
    if not get_admin_from_cookie(request):
        return RedirectResponse(url='/admin')
    return templates.TemplateResponse('admin/edit.html', {'request': request, 'post': None})


@app.post('/admin/new')
def admin_new(request: Request, title: str = Form(...), content: str = Form('')):
    # simple admin guard via cookie
    if request.cookies.get('is_admin') != '1':
        raise HTTPException(status_code=403)
    db = SessionLocal()
    slug = make_slug(title)
    post = Post(title=title, slug=slug, content=content)
    db.add(post)
    db.commit()
    db.close()
    return RedirectResponse(url='/admin/list', status_code=302)


@app.get('/admin/edit/{post_id}', response_class=HTMLResponse)
def admin_edit_page(request: Request, post_id: int):
    if not get_admin_from_cookie(request):
        return RedirectResponse(url='/admin')
    db = SessionLocal()
    post = db.query(Post).get(post_id)
    db.close()
    if not post:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse('admin/edit.html', {'request': request, 'post': post})


@app.post('/admin/edit/{post_id}')
def admin_edit(request: Request, post_id: int, title: str = Form(...), content: str = Form('')):
    if request.cookies.get('is_admin') != '1':
        raise HTTPException(status_code=403)
    db = SessionLocal()
    post = db.query(Post).get(post_id)
    if not post:
        db.close()
        raise HTTPException(status_code=404)
    post.title = title
    post.content = content
    db.commit()
    db.close()
    return RedirectResponse(url='/admin/list', status_code=302)


@app.post('/admin/delete/{post_id}')
def admin_delete(request: Request, post_id: int):
    if request.cookies.get('is_admin') != '1':
        raise HTTPException(status_code=403)
    db = SessionLocal()
    post = db.query(Post).get(post_id)
    if post:
        db.delete(post)
        db.commit()
    db.close()
    return RedirectResponse(url='/admin/list', status_code=302)
