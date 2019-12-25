"""
    博客蓝图

    为蓝图增加蓝图的路由的两种方式：
        1. 使用装饰器，蓝图对象.route()  -->  先将路由注册到蓝图对象上，当将蓝图对象注册到程序实例上的时候，在将路由注册到程序实例上

            对于蓝图对象的理解：
                1。 蓝图对象是一种命名空间，使用蓝图对象添加的路由，都属于蓝图对象的命名空间上，可以通过app.url_map()来查看
                    Rule('/index'),  蓝图对象.endpoint  view_func()
                2.  使用蓝图对象可以实现项目结构的有序化的组织，可以将程序分离成不同的部分
        2. app.add_url_rule(rule, endpoint, view_func)
            在路由中，视图函数和url规则不是直接映射的，之所以不直接映射，是为了实现蓝图的命名空间
            如果存在多个同名的视图函数，会存在路由的冲突，增加了端点名作为媒介，可以实现不同命名空间的映射

    paginate()分页的使用：
        1。 接受的参数：page --> 页数  per-page --> 每页的个数， error_out ---> 当查询的页数超过总页数的行为
            max_per_page --> 设置每页查询的最大数量
            当error_out参数设置为True的时候，如果查询的页数超过最大值，或者是page或者per_page为负数或者非整型值的时候
            会返回404错误，如果设置为False，直接返回None，默认是True

        2. 对查询结果使用paginate方法传入相应的参数，可以返回一个分页对象，包含分页的信息
            分页对象一些常见的属性：
                has_next  --->    是否包含下一页，包含的时候返回True，不包含的时候返回False
                has_prev  --->    是否包含上一页，包含返回true，不包含返回false
                items     --->    返回分页之后的数据
                next_num  --->    下一页的页数，没有下一页返回None
                prev_num  --->    上一页的页数，没有上一页返回None
                page      --->    当前的页数
                pages     --->    总页数
                per_page  --->    每页的个数
                query     --->    分页的查询语句
                total     --->    总的记录的数量
            如果没有指定page参数和per_page参数，flask_sqlalchemy会自动从查询字符串中寻找对应的值
            如果没有获取到，，使用默认值，page=1，per_page=20
"""

from flask import Blueprint
from flask import request
from flask import current_app
from flask import render_template
from flask import abort
from flask import make_response
from flask import flash
from flask import redirect
from flask import url_for
from flask_login import current_user

from blog.models import Post, Category, Comment
from blog.utils import redirect_back
from blog.forms import AdminCommentForm, CommentForm
from blog.extensions import db

blog_bp = Blueprint('blog', __name__)


@blog_bp.route('/')
def index():
    """首页视图"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLUELOG_POST_PER_PAGE']
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, per_page=per_page)  # 生成一个分页对象
    posts = pagination.items   # 获取经过分页的数据

    return render_template('blog/index.html', pagination=pagination, posts=posts)


@blog_bp.route('/about')
def about():
    """展示关于的信息"""
    return render_template('blog/about.html')


@blog_bp.route('/category/<int:category_id>', methods=["GET"])
def show_category(category_id):
    """
        分类文章列表(边栏的分页文章)

        直接调用category.posts，会以列表的形式返回分类对应的文章，但是无法再次使用查询过滤器
        使用with_parent方法会返回查询的对象，可以链式调用查询过滤器
    :param category_id: 分类id
    :return:
    """
    category = Category.query.get_or_404(category_id)  # 获取当前的分类
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLUELOG_POST_PER_PAGE']

    # 获取分页对象
    pagination = Post.query.with_parent(category).order_by(
        Post.timestamp.desc()).paginate(page, per_page=per_page)

    # 获取分页数据
    posts = pagination.items

    return render_template(
        'blog/category.html', pagination=pagination, category=category, posts=posts
    )


@blog_bp.route('/show_post/<int:post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    """博客文章视图"""

    post = Post.query.get_or_404(post_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLUELOG_COMMENT_PER_PAGE']

    # 显示已经通过审核的评论
    pagination = Comment.query.with_parent(post).filter_by(reviewed=True).order_by(
        Comment.timestamp.asc()).paginate(page, per_page)
    comments = pagination.items

    if current_user.is_authenticated:
        """如果当前的用户已经登陆，使用管理员的表单"""
        form = AdminCommentForm()
        form.author.data = current_user.name
        form.email.data = current_app.config['BLUELOG_EMAIL']
        form.site.data = url_for('.index')
        from_admin = True
        reviewed = True

    else:
        form = CommentForm()
        from_admin = False
        reviewed = False

    if form.validate_on_submit():
        """当表单认证通过的时候执行的操作"""
        author = form.author.data
        email = form.email.data
        site = form.email.data
        body = form.body.data
        comment = Comment(
            author=author, email=email, site=site, body=body,
            from_admin=from_admin, post=post, reviewed=reviewed
        )
        reply_id = request.args.get('reply')
        if reply_id:
            comment = Comment.query.get_or_404(reply_id)
            comment.replied_id = reply_id

        db.session.add(comment)
        db.session.commit()

        if current_user.is_authenticated:
            flash('评论成功')

        else:
            flash('你的评论已经提交，等待管理员的审核')
            # send_comment_email(post)  # 发送邮件
        return redirect(url_for('.show_post', post_id=post_id))

    return render_template(
        '/blog/post.html', post=post, pagination=pagination,
        comments=comments, form=form
    )


@blog_bp.route('/change-theme/<theme_name>')
def change_theme(theme_name):
    """
        博客切换主体视图
        1.  将主题的名称存储在cookie中，名称为theme
    :param theme_name: 主体名
    :return:
    """
    # 判断配置项是否合法
    if theme_name not in current_app.config['BLUELOG_THEMES'].keys():
        abort(400)

    response = make_response(redirect_back())

    # set_cookie方法接受key ---> cookie名  value=""  --> cookie值, max_age=None, 过期时间  expires=None  --> 有效期,
    # 这里设置cookie的过期时间为30天
    response.set_cookie('theme', theme_name, max_age=30*24*60*60)

    return response


@blog_bp.route('/reply/comment/<int:comment_id>')
def reply_comment(comment_id):
    """
        回复评论
    :param comment_id: 评论id
    :return:
    """

    comment = Comment.query.get_or_404(comment_id)
    if not comment.post.can_comment:
        """如果当前评论对应的文章不支持评论"""
        flash('当前文章不支持评论，请申请管理员开启评论')
        return redirect(url_for('.show_post', post_id=comment.post_id))

    return redirect(
        url_for('.show_post', post_id=comment.post_id, reply=comment_id, auth=comment.author)
    )