from flask_mail import Message
from flask import render_template
from flask import current_app
from blog.extensions import mail
from blog.celery_tasks.main import celery_app


@celery_app.task(name='send_mail')
def send_mail(subject, to, template, **kwargs):
    message = Message(subject, recipients=[to])
    message.body = render_template(template + '.txt', **kwargs)
    message.html = render_template(template + '.html', **kwargs)
    app = current_app
    with app.app_context():
        mail.send(message)


def send_confirm_email(user, token, to=None):
    """发送确认邮件"""
    send_mail(subject='确认邮件', to=to or user.email, template='emails/confirmed', user=user, token=token)


def resend_confirm_email(user, token, to=None):
    """重新发送确认邮件"""
    send_mail(subject='确认邮件', to=to or user.email, template='emails/confirmed', user=user, token=token)