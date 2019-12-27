"""
    定义数据库模型类
"""
from datetime import datetime

from flask_avatars import Identicon

from blog.extensions import db

from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import UserMixin


# secret_string = Serializer(current_app.config['SECRET_KEY'], expires_in=3600)  # 生成一个对象
# token = secret_string.dumps({'confirm': 23})  # 生成密钥令牌字符串
# secret_string = secret_string.loads(token)  # 解码令牌，成功则返回原始数据，此方法会验证签名和有效期


class Admin(db.Model, UserMixin):
    """管理员模型类"""

    __tablename__ = 'admins'  # 自定义表名

    id = db.Column(db.Integer, primary_key=True)  # id主键
    name = db.Column(db.String(30), comment='管理员姓名')  # 管理员姓名
    username = db.Column(db.String(20), comment='管理员用户名')  # 管理员用户名
    password_hash = db.Column(db.String(128), comment='密码')  # 管理员密码hash值
    blog_title = db.Column(db.String(60), comment='博客标题')  # 博客标题
    blog_sub_title = db.Column(db.String(100), comment='博客副标题')  # 博客副标题
    about = db.Column(db.Text, comment='关于')  # 关于
    confirmed = db.Column(db.Boolean, default=False, nullable=False, comment='是否确认')
    email = db.Column(db.String(40), comment='邮箱地址')
    avatar_s = db.Column(db.String(64))  # 小尺寸图片
    avatar_m = db.Column(db.String(64))  # 中尺寸图片
    avatar_l = db.Column(db.String(64))  # 大尺寸图片
    avatar_raw = db.Column(db.String(64))  # 图片描述

    def __init__(self, **kwargs):
        """
            初始化生成用户的时候，设置一个默认的头像
        """
        super(Admin, self).__init__(**kwargs)
        self.generate_avatar()

    def generate_avatar(self):
        """生成默认的头像"""
        avatar = Identicon()
        filenames = avatar.generate(text=self.username)
        self.avatar_s = filenames[0]
        self.avatar_m = filenames[1]
        self.avatar_l = filenames[2]
        db.session.commit()

    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        """校验密码"""
        return check_password_hash(self.password_hash, password)
    # 设置密码的另一种实现方式
    @property
    def password(self):
        raise AttributeError('该属性不可读')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)


class Category(db.Model):
    """分类模型类"""

    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, comment='分类名称')  # 分类名称

    posts = db.relationship(
        'Post', backref='category', cascade='all, delete-orphan')  # 定义关系

    def delete(self):
        """删除分类的时候，将文章的分类置为默认分类"""
        default_category = Category.query.get(1)
        posts = self.posts[:]
        for post in posts:
            post.category = default_category
        db.session.delete(self)
        db.session.commit()


class Post(db.Model):
    """文章模型类"""

    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60), comment='文章的标题')  # 文章的标题
    body = db.Column(db.Text(), comment='文章主体')  # 文章主体
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, index=True, comment='创建时间'
    )  # 创建时间
    can_comment = db.Column(db.Boolean, default=1, comment='可以评论')  # 是否可以评论
    slug = db.Column(db.String(90), comment='固定链接')  # 固定链接字段

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))  # 定义外键
    comments = db.relationship(
        'Comment', backref='post', cascade='all, delete-orphan')  # 定义关系


class Comment(db.Model):
    """评论模型类"""

    __tablename__ = 'comments'  # 指定表名

    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(30), comment='评论作者')  # 评论的作者
    email = db.Column(db.String(254), comment='评论的邮箱地址')  # 评论的邮箱地址
    site = db.Column(db.String(255), comment='评论的站点')  # 站点
    body = db.Column(db.Text, comment='评论的内容')  # 评论的内容
    from_admin = db.Column(
        db.Boolean, default=False, comment='评论是否来自管理员'
    )  # 是否来自管理员
    reviewed = db.Column(
        db.Boolean, default=False, comment='评论是否经过审核'
    )  # 评论是否经过审核
    timestamp = db.Column(
        db.DateTime, default=datetime.utcnow, index=True, comment='评论的创建时间'
    )  # 评论的创建时间

    replied_id = db.Column(db.Integer, db.ForeignKey('comments.id'))  # 定义外键指向自身
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))  # 定义外键指向post
    replies = db.relationship(
        'Comment', backref='replied', remote_side=[id],
        single_parent=True, cascade='all, delete-orphan'
    )  # remote_side在邻接列表关系中指定多的一侧


class Link(db.Model):
    """链接模型类"""

    __tablename__ = 'links'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), comment='链接名')
    url = db.Column(db.String(255), comment='链接的url')

