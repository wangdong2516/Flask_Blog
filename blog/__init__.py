"""
    初始化操作
"""
import logging
import os
from logging.handlers import SMTPHandler, RotatingFileHandler

import click
from flask import Flask, render_template, request
from flask_login import current_user
from flask_sqlalchemy import get_debug_queries
from flask_wtf.csrf import CSRFError
from flask import url_for
from celery import Celery

from blog.blueprints.admin import admin_bp
from blog.blueprints.auth import auth_dp
from blog.blueprints.blog import blog_bp
from blog.extensions import bootstrap, db, login_manager
from blog.extensions import csrf, ckeditor, mail, moment, toolbar, migrate, avatars
from blog.models import Admin, Post, Category, Comment, Link
from blog.settings import config

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def create_app(config_name=None):
    """"""
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')

    app = Flask('blog')
    app.config.from_object(config[config_name])
    # register_logging(app)
    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    register_errors(app)
    register_shell_context(app)
    register_template_context(app)
    register_request_handlers(app)
    print(app.url_map)
    return app


# def register_logging(app):
#     """注册日志记录"""
#     class RequestFormatter(logging.Formatter):
#
#         def format(self, record):
#             record.url = request.url
#             record.remote_addr = request.remote_addr
#             return super(RequestFormatter, self).format(record)
#
#     request_formatter = RequestFormatter(
#         '[%(asctime)s] %(remote_addr)s requested %(url)s\n'
#         '%(levelname)s in %(module)s: %(message)s'
#     )
#
#     formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#
#     file_handler = RotatingFileHandler(os.path.join(basedir, 'logs/bluelog.log'),
#                                        maxBytes=10 * 1024 * 1024, backupCount=10)
#     file_handler.setFormatter(formatter)
#     file_handler.setLevel(logging.INFO)
#
#     mail_handler = SMTPHandler(
#         mailhost=app.config['MAIL_SERVER'],
#         fromaddr=app.config['MAIL_USERNAME'],
#         toaddrs=['ADMIN_EMAIL'],
#         subject='Bluelog Application Error',
#         credentials=(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']))
#     mail_handler.setLevel(logging.ERROR)
#     mail_handler.setFormatter(request_formatter)
#
#     if not app.debug:
#         app.logger.addHandler(mail_handler)
#         app.logger.addHandler(file_handler)


def register_shell_context(app):
    """注册shell执行环境"""
    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db, Admin=Admin, Post=Post, Category=Category, Comment=Comment)


def register_commands(app):
    """注册自定义命令"""

    @app.cli.command()
    @click.option('--drop', is_flag=True, help='Create after drop.')
    def initdb(drop):
        """初始化数据库"""
        if drop:
            click.confirm('This operation will delete the database, do you want to continue?', abort=True)
            db.drop_all()
            click.echo('Drop tables.')
        db.create_all()
        click.echo('Initialized database.....')

    @app.cli.command()
    @click.option('--username', prompt=True,  help='The username used to login.')
    @click.option(
        '--password', prompt=True, hide_input=True, confirmation_prompt=True,
        help='The password used to login.'
    )
    def init(username, password):
        """初始化管理员用户"""
        click.echo('初始化数据库>>>')
        db.create_all()

        admin = Admin.query.first()
        if admin:
            click.echo('管理员已经存在，正在更新>>>>')
            admin.username = username  # 赋值用户名
            admin.set_password(password)  # 设置密码

        else:
            click.echo('管理员不存在，正在创建>>>>')
            admin = Admin(
                name='Admin',
                username=username,
                blog_title='Bluelog',
                blog_sub_title="I'm the Best King James",
                about='ABout her'
            )
            admin.set_password(password)
            db.session.add(admin)

        category = Category.query.first()

        if not category:
            click.echo('文章分类还未创建，正在创建>>>>')
            category = Category(name='Default')
            db.session.add(category)

        db.session.commit()
        click.echo('完成初始化')

    @app.cli.command()
    @click.option('--category', default=10, help='创建分类')
    @click.option('--post', default=50, help='创建文章')
    @click.option('--comment', default=500, help='创建评论')
    def forge(category, post, comment):
        """
            生成项目需要的虚拟数据
        :param category: 分类名
        :param post: 文章
        :param comment: 评论
        :return:
        """

        from blog.fakes import fake_admin, fake_categories, fake_posts, fake_comments, fake_links

        db.drop_all()
        db.create_all()

        click.echo('开始创建管理员用户')
        fake_admin()

        click.echo('开始创建分类')
        fake_categories(category)

        click.echo('开始创建文章')
        fake_posts(post)

        click.echo('开始创建评论')
        fake_comments(comment)

        click.echo('开始创建链接')
        fake_links()

        click.echo('虚拟数据创建完成')


def register_request_handlers(app):
    """
        注册请求处理函数
            1。 请求钩子的作用就是进行一些额外的处理
            2。 使用蓝图对象注册的请求钩子，只会被蓝图对象的路由触发，可以在蓝图对象中注册全局的请求处理函数
                使用@蓝图对象.before_app_request,after_app_request
            3. @app.before_request注册的请求钩子可以注册全局的请求处理函数
    :param app:
    :return:
    """
    @app.after_request
    def query_profiler(response):
        for q in get_debug_queries():
            if q.duration >= app.config['BLUELOG_SLOW_QUERY_THRESHOLD']:
                app.logger.warning(
                    'Slow query: Duration: %fs\n Context: %s\nQuery: %s\n '
                    % (q.duration, q.context, q.statement)
                )
        return response


def register_template_context(app):
    """
        注册模板上下文处理函数
        1。 蓝图对象可以使用app.context_processor装饰器为模板注册模板上下文处理函数，模板上下文处理函数的作用就是
            为模板添加一些在模板中需要使用的变量，这样可以避免每次显示的传入模板
        2。 同样的，使用蓝图对象注册的模板上下文，只可以在特有的蓝图模板中使用，也可以使用蓝图对象.app_context_processor
            注册全局的模板上下文处理函数
        3。 蓝图对象也可以使用app_template_global(), app_template_filter(), app_template_test()装饰器，用来注册
            全局的模板全局函数，模板过滤器和模板测试器
    """

    @app.context_processor
    def make_template_context():
        admin = Admin.query.first()
        categories = Category.query.order_by(Category.name).all()
        links = Link.query.order_by(Link.name).all()
        if current_user.is_authenticated:
            # current_user.is_authenticated是flask_login提供的，当用户登陆认证成功之后，返回True
            unread_comments = Comment.query.filter_by(reviewed=False).count()
        else:
            unread_comments = None
        return dict(
            admin=admin, categories=categories,
            links=links, unread_comments=unread_comments)


def register_errors(app):
    """
        注册错误处理函数
        注意：
            1。 使用蓝图对象.errorhandler装饰器注册的错误处理函数，只能捕捉访问蓝图对象中的路由时发生的错误
            2。 使用蓝图对象的app_errorhandler装饰器可以注册一个全局的错误处理函数
            3。 404和405错误仅会被全局的错误处理函数所捕捉，如果想区分错误是否来自视图函数，可以根据request.path.startswith()来判断
            4。 app.errorhandler()接受错误状态码作为参数，表示捕捉指定的错误
    """

    @app.errorhandler(400)
    def error_400(e):
        """自定义400错误的处理"""
        return render_template('errors/400.html')

    @app.errorhandler(403)
    def error_403(e):
        """403错误处理"""
        return render_template('errors/403.html')

    @app.errorhandler(404)
    def error_404(e):
        """自定义404错误的处理"""
        return render_template('errors/404.html', url_for=url_for)

    @app.errorhandler(500)
    def error_500(e):
        return render_template('errors/500.html')

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        """自定义csrf验证错误"""
        return render_template('errors/400.html', description='会话过期或者失效'), 400


def register_extensions(app):
    """初始化一系列的扩展"""
    bootstrap.init_app(app)  # Bootstarp扩展
    db.init_app(app)  # salalchemy扩展
    ckeditor.init_app(app)  # 富文本编辑器扩展
    csrf.init_app(app)  # csrf扩展
    login_manager.init_app(app)  # flask_login扩展
    mail.init_app(app)  # 电子邮件扩展
    moment.init_app(app)  # flask_moment本地化时间扩展
    toolbar.init_app(app)  # 调试工具扩展
    migrate.init_app(app, db)  # 数据库迁移扩展,必须传递db作为第二个参数
    avatars.init_app(app)  # 头像


def register_blueprints(app):
    """注册蓝图对象的函数

        蓝图使用app.register_blueprint()方法进行注册，必须传入的参数是创建的蓝图对象，其他的参数是用来控制蓝图的行为
        比如使用url_prefix参数为蓝图下的所有视图url附加一个url前缀
        此时蓝图下的视图url都会增加一个/auth前缀
        使用subdomain参数可以为蓝图下的路由设置子域名
            app.register_blueprint(auth_dp, url_prefix='/auth', subdomain='auth')

        端点作为url规则和视图函数的中间媒介
        使用app.route()可以给视图函数注册一个路由，使用app.add_url_rule()方法同样也可以注册路由

        app.add_url_rule(rule, endpoint, view_func) 的第二个参数指定端点，第三个参数是视图函数对象
        在路由中，url规则和视图函数不是直接映射的，而是通过端点作为中间媒介
        不直接映射url和视图函数，原因是使用端点可以实现蓝图中的视图函数的命名空间

        一旦使用蓝图，我们就要对url_for()函数中的端点值进行修改，添加蓝图实例名来明确端点的归属
        端点也有一种简写的方式，在蓝图内部可以使用.视图函数的形式来省略蓝图的名称，但是在全局环境中，必须使用完整的名称

        使用蓝图可以避免端点值的重复冲突，但是路由的url规则还是会产生重复，当两个蓝图中有相同的url规则的时候，
        请求只会分配到第一个注册的蓝图对象上，我们可以通过使用url_prefix参数指定前缀的方式解决

        要使用蓝图独有的静态文件，需要在定义蓝图的时候，使用static_folder参数指定蓝图静态文件夹的位置
        参数值可以是绝对路径或者是相对路径，另外，因为蓝图内置的static路由和程序实例的static路由是相同的，
        我们需要使用static_url_path参数为蓝图对象指定新的静态文件路由,如果在创建蓝图对象的时候，制定了url
        前缀的话，这里static_url_path会自动变为/前缀/static
            auth_dp = Blueprint('auth', __name__, static_floder='static', static_url_path='auth/static')
        在生成用来获取蓝图静态文件的url的时候，需要写出完整的端点

        当蓝图中包含独特的模板文件夹的时候，在实例化蓝图对象的时候，使用tempalte_folder参数指定模板文件夹的位置



        默认情况下，端点是视图函数名称，我们也可以使用endpoint参数改变
    """
    app.register_blueprint(blog_bp)
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(auth, url_prefix='/auth')  # 注册蓝图给程序实例app
