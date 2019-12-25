"""
    表单类的定义
"""
from flask_ckeditor import CKEditorField
from blog.models import Category
from flask_wtf import FlaskForm  # 导入表单类
from wtforms import IntegerField, SubmitField, StringField, SelectField, TextAreaField, HiddenField  # 导入表单字段
from wtforms import BooleanField, PasswordField, ValidationError  # 导入表单字段
from wtforms.validators import DataRequired, URL, Length, Email, Optional, EqualTo  # 导入验证函数
from blog.models import Admin

class LoginForm(FlaskForm):
    """
        登陆表单类
        表单类属性将渲染成表单的name和id属性
        实例化表单字段传入的第一个参数将渲染为展示的字段名
    """
    username = StringField('用户名', validators=[DataRequired(), Length(1, 20)])  # 用户名字段
    password = PasswordField('密码', validators=[DataRequired(), Length(1, 128)])  # 密码字段
    password_ = PasswordField(
        '确认密码', validators=[DataRequired(), Length(1, 128),
                                 EqualTo('password', message='密码输入错误，请重新输入')]
    )  # 确认密码
    remember = BooleanField('记住密码')  # 记住密码
    submit = SubmitField('登陆')  # 提交按钮


class SettingForm(FlaskForm):
    name = StringField('姓名', validators=[DataRequired(), Length(1, 30)])
    blog_title = StringField('博客标题', validators=[DataRequired(), Length(1, 60)])
    blog_sub_title = StringField('博客副标题', validators=[DataRequired(), Length(1, 100)])
    about = CKEditorField('关于', validators=[DataRequired()])
    submit = SubmitField('提交')


class CommentForm(FlaskForm):
    """评论表单"""

    author = StringField('姓名', validators=[DataRequired(), Length(1, 30)])  # 姓名(作者)
    email = StringField('邮箱', validators=[DataRequired(), Email(), Length(1, 254)])  # 邮箱
    site = StringField('站点', validators=[Optional(), URL(), Length(0, 255)])
    body = TextAreaField('内容', validators=[DataRequired()])
    submit = SubmitField()


class AdminCommentForm(CommentForm):
    """管理员评论表单，管理员评论不需要姓名，电子邮箱等字段"""

    author = HiddenField()
    email = HiddenField()
    site = HiddenField()


class RegisterForm(FlaskForm):
    """注册表单"""
    name = StringField('姓名', validators=[DataRequired(), Length(1, 30)])
    username = StringField('用户名', validators=[DataRequired(), Length(1, 20)])
    password = PasswordField('密码', validators=[DataRequired(), EqualTo('password2'),
                                               Length(8, 128)])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    email = StringField('邮箱', validators=[Email(), DataRequired()])
    blog_title = StringField('博客标题', validators=[DataRequired(), Length(5, 30)])
    blog_sub_title = StringField('博客副标题', validators=[DataRequired(), Length(6, 40)])
    about = StringField('关于', validators=[Optional()])
    submit = SubmitField('提交')

    def validate_username(self, field):
        """验证用户名"""
        user = Admin.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError('该用户名已经存在，请重新输入')


class PostForm(FlaskForm):
    """
        撰写文章的表单

        下拉列表字段通过SelectField类来表示一个select标签，
        下拉列表的选项通过参数choices指定，choices参数必须是一个包含两个元素的元祖列表
        列表中的元素分别包含选项值和选项标签

        使用coerce关键字指定数据类型，默认是字符串
        default参数设置默认的选项值

        在构造方法__init__方法中指定choices和在实例化的时候指定choices参数的效果是一样的
    """

    title = StringField('标题', validators=[DataRequired(), Length(1, 60)])
    category = SelectField('分类', coerce=int, default=1)
    body = CKEditorField('正文', validators=[DataRequired()])
    submit = SubmitField('提交')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)  # 调用父类的初始化方法
        self.category.choices = [
            (category.id, category.name) for category in Category.query.order_by(Category.name).all()
        ]  # 指定下拉内容


class CategoryForm(FlaskForm):
    """编辑分类的表单"""

    name = StringField('分类名称', validators=[DataRequired(), Length(1, 35, message='输入的分类名称为1～35个字符')])
    submit = SubmitField('提交')

    def validate_name(self, field):
        """验证分类名称是否已经存在"""
        if Category.query.filter(Category.name == field.data).first():
            raise ValidationError(message='分类名称已经存在')


class LinkForm(FlaskForm):
    """链接编辑表单"""
    name = StringField('名称', validators=[DataRequired(), Length(1, 30)])
    url = StringField('链接', validators=[DataRequired(), URL(), Length(1, 255)])
    submit = SubmitField()

