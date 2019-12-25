"""
    存储各种辅助函数
"""

try:
    from urlparse import urlparse, urljoin
except ImportError:
    from urllib.parse import urlparse, urljoin

from flask import request
from flask import redirect
from flask import url_for, current_app
from blog.extensions import db
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer  # 生成签名
from itsdangerous import SignatureExpired, BadSignature


def is_safe_url(target):
    """
        判断是否为安全的url

        urlparse包的使用：
            1。 作用解析url，将url解析为一个六元素的元祖
                scheme: 使用的协议
                netloc：主机地址
                path：请求的路径
                params：传递的参数
                query: 查询字符串
                fragment： 片段
    :return:
    """
    host_url = urlparse(request.host_url)
    target_url = urlparse(urljoin(request.host_url, target))

    return target_url.scheme in ('http', 'https') and host_url.netloc == target_url.netloc


def redirect_back(default='blog.index', **kwargs):
    """重定向到上一个页面"""
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue

        if is_safe_url(target):
            return redirect(target)

    return redirect(url_for(default, **kwargs))


def commit_data(do, obj):
    """
        提交修改到数据库
    :param do: 希望进行的操作 add 表示增加或者是更新
    :param obj: 提交的数据对象
    :return:
    """
    if do == 'add':
        db.session.add(obj)
    else:
        db.session.delete(obj)
    db.session.commit()


def generate_confirmation_token(user, op, expiration=3600):
    """生成加密令牌"""
    s = Serializer(current_app.config['SECRET_KEY'], expiration)  # 生成加密令牌并且指定令牌的有效期

    return s.dumps({'confirm': user.id, 'operations': op})  # 将用户id进行签名之后返回


def confirm_token(user, token, op):
    """
        验证令牌的正确性和有效期
    :param token: 加密之后的令牌值
    :return:
    """

    s = Serializer(current_app.config['SECRET_KEY'])

    try:
        data = s.loads(token)
    except (BadSignature, SignatureExpired) as e:
        return False
    if data.get('confirm') != user.id or data.get('operations') != op:
        return False
    user.confirmed = True
    commit_data('add', user)
    return True