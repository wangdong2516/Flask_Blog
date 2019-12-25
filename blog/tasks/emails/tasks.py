"""
    存储发送电子邮件的函数
"""
from flask_mail import Message
from flask import current_app
from flask import render_template
from tasks.main import celery_app
from blog.extensions import mail


@celery_app.task(name='_send_async_mail')
def _send_async_mail(to, subject, template, **kwargs):
    """
        使用celery异步发送邮件
    :param to:
    :param subject:
    :param template:
    :param kwargs:
    :return:
    """
    message = Message(
        subject=subject, recipients=[to]
    )
    # Message类的构造函数接受的参数： subject表示邮件的标题
    # recipients表示收件人列表， sender表示发件人，如果配置了MAIL_DEFAULT_SENDER，
    # 将使用该配置项作为默认的发件人使用
    message.body = render_template(template + '.txt', **kwargs)  # 发送text格式的邮件
    message.html = render_template(template + '.html', **kwargs)  # 发送html格式的邮件
    app = current_app._get_current_object()  # 获取被代理的程序实例
    with app.app_context():
        """手动开启上下文"""
        mail.send(message)


def send_confirm_email(user, token, to=None):
    """
        发送帐号确认邮件
    :param user: 用户
    :param token: 验证签名
    :param to: 收件人
    :return:
    """
    _send_async_mail.delay(to=to, subject='确认邮件', template='emails/confirmed', user=user, token=token)


def resend_confirm_email(user, token, to=None):
    """
        重新发送确认邮件
    :param user: 用户
    :param token: 签名
    :param to: 收件人
    :return:
    """
    _send_async_mail.delay(to=to, subject='重新确认邮箱', template='emails/reconfirmed', user=user, token=token)