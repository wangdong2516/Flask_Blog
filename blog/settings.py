"""项目的配置文件"""

import os
from dotenv import load_dotenv
load_dotenv()
# 项目的基本目录
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class BaseConfig(object):
    """
        基本配置类
    """
    SECRET_KEY = os.getenv('SECRET_KEY', 'secret string')  # 项目密钥

    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 自动追踪修改

    MAIL_SERVER = os.getenv('MAIL_SERVER')  # 电子邮件服务器
    MAIL_PORT = 465  # 发信端口
    MAIL_USE_SSL = True  # 是否使用SSL/TLS
    MAIL_USE_TLS = False  # 是否使用STARTTLS  163邮箱不支持
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')  # 发信服务器的用户名
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')  # 发信服务器的密码
    MAIL_DEFAULT_SENDER = ('FlaskBlog Admin', MAIL_USERNAME)  # 默认发件人(用户名， 地址)

    BLUELOG_EMAIL = os.getenv('BLUELOG_EMAIL')  # 博客邮件
    BLUELOG_POST_PER_PAGE = 10  # 博客页面每页的个数，使用环境变量配置可以实现动态修改
    BLUELOG_MANAGE_POST_PER_PAGE = 15  # 管理后台的每页的个数
    BLUELOG_COMMENT_PER_PAGE = 15  # 评论数

    # bootstarp主体样式配置  主体名称：显示名称
    BLUELOG_THEMES = {'perfect_blue': 'Perfect Blue', 'black_swan': 'Black Swan'}
    BLUELOG_SLOW_QUERY_THRESHOLD = 1

    BLUELOG_UPLOAD_PATH = os.path.join(basedir, 'uploads')
    BLUELOG_ALLOWED_IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
    CKEDITOR_FILE_UPLOADER = 'admin_bp.upload'  # 指定编辑器上传文件的处理函数
    # CKEDITOR_SERVE_LOCAL = True
    CKEDITOR_ENABLE_CSRF = True  # 配置富文本编辑器禁用CSRF
    UPLOADED_PATH = os.path.join(basedir, 'uploads')  # 指定上传文件的保存路径


class DevelopmentConfig(BaseConfig):
    """开发环境配置"""

    SQLALCHEMY_DATABASE_URI = 'mysql://root:wang1277@localhost/flask'


class TestingConfig(BaseConfig):
    """测试环境配置"""

    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'mysql://root:wang1277@host/Test'


class ProductionConfig(BaseConfig):
    """生产环境配置"""

    SQLALCHEMY_DATABASE_URI = 'mysql://root:wang1277@127.0.0.1:3307/flask'


# 建立配置类的映射，用于在创建程序实例的时候通过配置的名称创建对应的配置类，创建程序实例之后，使用app.config.from_object()
# 从对象中加载配置

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

# 存储一些通用的操作
class Operations:

    CONFIRM  = 'confirm'