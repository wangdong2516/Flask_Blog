"""
    存储扩展实例化的操作

    flask_login扩展：
        1。 使用：
            安装： pip install flask-login
            初始化： login_manager = LoginManager(app)
        2.  要求：
            要求表示用户的类中必须实现一下的方法和属性，以便判断用户的登录状态

            is_authenticated: 如果已经通过认证，返回True，否则返回False
            is_active: 如果允许用户登录，返回True，否则返回False
            is_anonymous: 如果当前用户未登录，返回True，否则返回False
            get_id()：以Unicode形式返回用户的唯一标示符
        3。 UserMixin表示已经登录并且通过认证的用户，is_authenticated和is_active会返回True，is_anonymous返回False
            get_id()默认会查找用户对象的id属性值作为id
        4。 使用flask-login实现用户登录和登出是十分简单的，只需要调用login_user()和logout_user()即可
            传入要登录或者是要登出的用户对象
            原理：
                flask-login使用flask的session对象将用户id存储在cookie中，名为user_id
                通过将login_user()参数remember设置为True，会在浏览器中创建一个名为remember_token的cookie
                当user_id的cookie失效之后，会重新恢复user_id的值
        5。 current_user对象，是一个代理对象表示当前用户，调用的时候会返回当前的用户对应的模型类对象
            使用flask_login需要实现用户加载函数，使用login_manager.user_loader装饰器实现，接受用户id作为参数，返回对应的
            用户对象
"""
from flask_sqlalchemy import SQLAlchemy  # 数据库扩展
from flask_bootstrap import Bootstrap  # Bootstrap扩展
from flask_mail import Mail  # 电子邮件扩展
from flask_ckeditor import CKEditor  # 富文本编辑器扩展
from flask_login import LoginManager  # 登陆认证扩展
from flask_wtf import CSRFProtect  # csrf表单扩展
from flask_avatars import Avatars
# """
#     CSRFProtect是flask-wtf内置的提供CSRF保护的扩展，可以实现CSRF保护，它主要提供了生成和验证CSRF令牌的函数，可以在不使用
#     WTForms表单类的情况下实现CSRF保护
#
#     CSRFProtect在模板中提供了csrf_token()函数，用来生成CSRF令牌，我们可以直接在表单中渲染这个隐藏字段，将字段的name设置为csrf_token
#     在对应的视图函数中，可以直接执行删除操作，CSRFProtect会自动获取并且验证CSRF令牌的值
#     默认情况下，当令牌验证错误或者是令牌过期的时候，返回404错误，可以使用错误处理函数app.errorhandler处理
# """
from flask_moment import Moment  # 本地化时间扩展
from flask_debugtoolbar import DebugToolbarExtension  # 调试工具
from flask_migrate import Migrate  # 数据库迁移扩展


bootstrap = Bootstrap()
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()  # 实例化CSRF保护扩展
ckeditor = CKEditor()
mail = Mail()
moment = Moment()
toolbar = DebugToolbarExtension()
migrate = Migrate()
avatars = Avatars()  # 头像扩展

login_manager.login_view = 'auth.login'  # 用于设置未登录用户重定向的视图
login_manager.login_message_category = 'warning'  # 设置未登录消息的类别，默认类别为message
login_manager.login_message = '当前未登录，请先登录'  # 设置提示消息的内容


@login_manager.user_loader
def load_user(user_id):
    """
        加载当前用户的函数(flask_login实现)

        当在代码中调用current_user的时候，flask-login回调用用户加载函数返回对应的用户对象，
        如果当前的用户已经登录，返回用户类的实例，如果用户未登录，回返回匿名用户对象

        current_user存储在请求上下文的堆栈上，只有激活了请求上下文才可以使用
        我们可以对用户对象调用is_authenticated来判断当前用户的登录状态，is_aurhenticated被传入到模板的上下文中
        在模板中可以调用
    :param user_id: 用户id
    :return:
    """
    from blog.models import Admin
    user = Admin.query.get(user_id)
    return user