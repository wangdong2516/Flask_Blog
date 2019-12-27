"""
    存储各种辅助函数
"""

try:
    from urlparse import urlparse, urljoin
except ImportError:
    from urllib.parse import urlparse, urljoin

import os

from functools import wraps
from PIL import Image
from flask import request
from flask import redirect
from flask import flash
from flask import abort
from flask import url_for, current_app
from blog.extensions import db
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer  # 生成签名
from itsdangerous import SignatureExpired, BadSignature

from flask_login import current_user


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


def confirm_required(func):
    """验证用户是否确认账户的装饰器"""

    @wraps(func)
    def confirm(*args, **kwargs):

       if not current_user.confirmed:
           """如果当前用户未确认账户"""
           flash('当前功能只针对验证邮箱的用户开放', 'warning')
           abort(403)
       return func(*args, **kwargs)

    return confirm


def resize_avatar(image, filename, base_width):
    """裁剪头像"""
    # new_filename, ext = os.path.splitext(filename)
    new_image = Image.open(image)  # 打开一个图片
    width_precent = base_width / new_image.width  # 根据基本宽度确定需要缩小的百分比

    # 如果大于1表示不需要裁剪
    if width_precent >= 1:
        return filename

    height = new_image.size[1]
    new_height = height * width_precent
    img = new_image.resize((base_width, int(new_height)), Image.ANTIALIAS)
    img.save(os.path.join(
        current_app.config['AVATARS_SAVE_PATH'], filename),
        optimize=True, quality=85
    )  # 保存图片，并且压缩图片的大小
    return filename


