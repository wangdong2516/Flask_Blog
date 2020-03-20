"""
    蓝图对象是一个用于注册路由等操作的临时对象
    蓝图中的视图函数通过蓝图实例提供的route()装饰器注册
    使用蓝图实例的errorhandler()装饰器可以把错误处理器注册到蓝图上
    这些错误处理器只会处理访问该蓝图中的视图函数时发生的错误，使用蓝图实例的app_errorhandler()装饰器
    可以注册一个全局的错误处理器
        404和405错误仅会被全局的错误处理函数捕捉，如果区分蓝图url下的404和405错误
        可以在全局定义的404错误处理函数中使用request.path.statrswith(蓝图的url前缀)
        来判断请求的url是否属于某一个蓝图

    蓝图中，可以使用请求钩子注册的请求处理函数是蓝图独有的，只有蓝图中的视图函数会触发相应的请求处理函数
    另外，可以在蓝图中使用before_app_request, after_app_request,teardown_app_request, before_app_first_request方法
    这些方法注册的请求处理函数是全局的

    模板上下文处理函数
        使用context_processor装饰器注册蓝图特有的模板上下文处理器，使用app_context_processor装饰器则会注册程序全局的模板上下文处理器
        蓝图对象也可以使用app_template_global(), app_template_filter(), app_template_test()装饰器
        注册全局模板全局函数，模板过滤器函数和模板测试器

    并不是所有程序实例提供的方法和属性都可以在蓝图对象中使用，蓝图对象中只提供了少量用于注册处理函数的方法
    大部分的属性和方法仍然需要通过程序实例app获取，比如配置config属性和自定义注册命令的cli.command()装饰器

    为了使蓝图能够发挥作用，我们必须把蓝图注册到程序实例app上
"""

from flask import Blueprint, current_app
from flask import redirect, url_for
from flask import flash
from flask import render_template
from flask import send_from_directory

from flask_login import current_user, login_user, logout_user, login_required
from blog.celery_tasks.email.tasks import send_confirm_email, resend_confirm_email
from blog.forms import LoginForm, RegisterForm
from blog.models import Admin
from blog.utils import redirect_back, commit_data, generate_confirmation_token, confirm_token
from blog.settings import Operations


auth_dp = Blueprint('auth', __name__)


@auth_dp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登陆"""
    if current_user.is_authenticated:
        """如果用户经过认证,重定向到首页"""
        return redirect(url_for('blog.index'))

    form = LoginForm()  # 渲染登录的表单

    if form.validate_on_submit():
        """表单验证成功的逻辑"""
        username = form.username.data
        password = form.password.data
        remember = form.remember.data
        admin = Admin.query.filter_by(username=username).first()
        if admin:
            """验证用户名和密码"""
            if username == admin.username and admin.validate_password(password):
                login_user(admin, remember)  # 实现登陆用户的会话管理，记录用户的登陆状态
                flash('欢迎回来！！！')
                return redirect_back()  # 返回上一个页面
            else:
                flash('无效的用户名或者是密码')
        else:
            flash('不是管理员帐号')

    return render_template('auth/login.html', form=form)


@auth_dp.route('logout')
def logout():
    """
        用户登出 使用flask_login的logout()函数实现

        login_out()函数会登出用户并且清除session中存储的用户id和remember_token的值
    """

    logout_user()
    flash('退出成功')
    return redirect_back()


@auth_dp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    form = RegisterForm()

    if form.validate_on_submit():
        name = form.name.data
        username = form.username.data
        password = form.password.data
        blog_title = form.blog_title.data
        blog_sub_title = form.blog_sub_title.data
        about = form.about.data
        email = form.email.data
        # 添加一个用户
        admin = Admin(
            name=name, username=username, blog_title=blog_title,
            blog_sub_title=blog_sub_title, about=about, email=email
        )
        admin.set_password(password)
        commit_data('add', admin)
        token = generate_confirmation_token(user=admin, op=Operations.CONFIRM)  # 生成一个签名
        send_confirm_email(user=admin, token=token)  # 发送确认邮件
        flash('电子邮件已经发送，请注意查收！', 'success')
        return redirect(url_for('.login'))
    return render_template('auth/register.html', form=form)


@auth_dp.route('/confirm/<path:token>')
@login_required
def confirm(token):
    """
        确认邮箱
    :param token: 签名
    :return:
    """
    if confirm_token(user=current_user, token=token, op=Operations.CONFIRM):
        """签名验证成功的逻辑"""
        flash('邮箱验证成功', 'success')
        return redirect(url_for('blog.index'))
    else:
        flash('邮箱验证失败！签名无效或者已经过期', 'warning')
        return redirect(url_for('.reconfirm_email'))


@auth_dp.route('/resend/email')
@login_required
def reconfirm_email():
    # 重新生成签名
    token = generate_confirmation_token(current_user, op=Operations.CONFIRM)
    # 重新发送短信验证码
    user = current_user
    resend_confirm_email(user, token=token)
    flash('邮件发送成功，请注意查收！', 'success')
    return redirect(url_for('.login'))


@auth_dp.route('/avatars/<path:filename>')
def get_avatar(filename):
    """
        获取用户头像,将目录中的文件返回
    :return:
    """
    return send_from_directory(current_app.config['AVATARS_SAVE_PATH'], filename)

