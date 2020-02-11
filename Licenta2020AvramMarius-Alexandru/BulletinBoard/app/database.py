from app.model import Post
from app import db


def get_all():
    posts = Post.query.all()
    if not posts:
        data = [dict(id=0, m=0, T=0, W=0, H=0, SW=0, SB=0)]
    else:
        data = [dict(id=post.id, m=post.m, T=post.T, W=post.W, H=post.H, SW=post.SW, SB=post.SB) for post in posts]
    return data


def get_id(id):
    posts = Post.query.filter(Post.id >= id)
    if not posts:
        return None
    data = [dict(id=post.id, m=post.m, T=post.T, W=post.W, H=post.H, SW=post.SW, SB=post.SB) for post in posts]
    return data


def get_writer_id(id, W):
    posts = Post.query.filter(Post.id >= id, Post.W == W)
    if not posts:
        return None
    data = [dict(id=post.id, m=post.m, T=post.T, W=post.W, H=post.H, SW=post.SW, SB=post.SB) for post in posts]
    return data


def delete():
    nr_del = db.session.query(Post).delete()
    db.session.commit()
    return nr_del


def get_writer(W):
    posts = Post.query.filter(Post.W == W)
    if not posts:
        return None
    data = [dict(id=post.id, m=post.m, T=post.T, W=post.W, H=post.H, SW=post.SW, SB=post.SB) for post in posts]
    return data


def get_last_id():
    pass


def insert(data):
    if data:
        # post = Post(m=data['m'], T=data['T'], W=data['W'], H=data['H'], SW=data['SW'], SB=data['SB'])
        post = Post(m=data['m'], T=data["T"], W=data['W'])
    else:
        raise AttributeError
    db.session.add(post)
    db.session.commit()
    db.session.refresh(post)
    return post.id


def error(err):
    print(err)
    db.session.rollback()
