"""
    存储虚拟数据生成函数，生成虚拟数据
"""
import random

from faker import Faker

from blog.models import Admin, Post, Comment, Category, Link
from blog.extensions import db
faker = Faker()


def fake_admin():
    """
        生成管理员的虚拟数据
    :return:
    """
    admin = Admin(
        username='admin',
        blog_title='Bluelog',
        blog_sub_title='I"m The Best King James',
        name='King James',
        about='I Am The Best'
    )
    admin.set_password('wangdong')
    db.session.add(admin)
    db.session.commit()


def fake_categories(count=10):
    """
        生成分类虚拟数据
    :param count: 数量
    :return:
    """

    category = Category(name='Default')  # 首先创建一个默认分类
    db.session.add(category)

    for i in range(1, count):
        category = Category(name=faker.word())
        db.session.add(category)
        try:
            db.session.commit()
        except:
            db.session.rollback()


def fake_posts(count=50):
    """
        生成文章虚拟数据
    :param count: 数量，通过命令行执指定或者使用默认值50
    :return:
    """
    for i in range(count):
        post = Post(
            title=faker.sentence()[:60],
            body=faker.text(200),
            category=Category.query.get(random.randint(1, Category.query.count())),
            timestamp=faker.date_time_this_year()
        )
        db.session.add(post)
    db.session.commit()


def fake_comments(count=500):
    """
        生成虚拟评论数据
    :param count: 评论的数据，没有指定使用默认值500
    :return:
    """
    for i in range(count):
        comment = Comment(
            author=faker.name(),
            email=faker.email(),
            site=faker.url(),
            body=faker.sentence(),
            timestamp=faker.date_time_this_year(),
            reviewed=True,
            post=Post.query.get(random.randint(1, Post.query.count()))
        )

        db.session.add(comment)

    salt = int(count * 0.1)
    for i in range(salt):
        """创建未回复的评论"""
        comment = Comment(
            author=faker.name(),
            email=faker.email(),
            site=faker.url(),
            body=faker.sentence(),
            timestamp=faker.date_time_this_year(),
            reviewed=False,
            post=Post.query.get(random.randint(1, Post.query.count()))
        )
        db.session.add(comment)

        comment = Comment(
            author='Mima Kirigoe',
            email='mima@example.com',
            site='example.com',
            body=faker.sentence(),
            timestamp=faker.date_time_this_year(),
            from_admin=True,
            reviewed=True,
            post=Post.query.get(random.randint(1, Post.query.count()))
        )
        db.session.add(comment)
    db.session.commit()

    for i in range(salt):
        """创建回复的评论"""
        comment = Comment(
            author=faker.name(),
            email=faker.email(),
            site=faker.url(),
            body=faker.sentence(),
            timestamp=faker.date_time_this_year(),
            reviewed=True,
            replies=Comment.query.get(random.randint(1, Post.query.count())),
            post=Post.query.get(random.randint(1, Post.query.count()))
        )
        db.session.add(comment)
    db.session.commit()


def fake_links():
    """生成虚拟链接数据"""
    twitter = Link(name='Twitter', url='#')
    facebook = Link(name='Facebook', url='#')
    linkedin = Link(name='LinkedIn', url='#')
    google = Link(name='Google+', url='#')
    db.session.add_all([twitter, facebook, linkedin, google])
    db.session.commit()
