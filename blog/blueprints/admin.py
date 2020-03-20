"""
    管理员

    url_for接受一个函数名作为参数，也接受对应url规则的命名变量
    未知的变量会添加到url尾部作为查询字符串

    flask中request对象的实现原理：
        1。 Thread Local
            每一个请求是一个独立的线程，请求之间的信息需要完全隔离开。避免冲突，实现线程安全
            Thread Local是一种特殊状态的对象，状态对于线程是隔离的，线程对Thread Local的修改
            并不会影响到其他的线程
        2. 主要的实现依赖于三个类：
            Local， LocalStack， LocalProxy

            __solts__类变量的作用是限制添加到实例对象上的属性
            __storage = {线程ID：{name: value}}
            线程ID通过掉用get_ident函数来实现

            比如：
                获取local.age属性的时候 --> 触发__getattr__函数
                内部调用get_ident函数获取当前线程的ID，然后去__storage
                字典中进行查找是否存在对应的属性
                设置属性的时候也是同理
            __release_local__ 就是将当前的线程从__storage字典中删除

"""

import os

from flask import Blueprint, send_from_directory
from flask import render_template
from flask import request
from flask import current_app
from flask import flash
from flask import redirect
from flask import url_for
from flask_dropzone import random_filename

from flask_login import login_required, current_user
from blog.models import Post, Category, Comment, Link, Admin
from blog.forms import PostForm, CategoryForm, LinkForm, SettingForm, UploadForm
from blog.extensions import db
from blog.utils import redirect_back, commit_data
from blog.utils import confirm_required
from blog.utils import resize_avatar
from flask_ckeditor import upload_fail, upload_success
admin_bp = Blueprint('admin_bp', __name__)  # 创建蓝图对象


@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@confirm_required
def settings():
    """
        博客的设置页面

        login_required装饰器实现了视图保护，只有登录之后的用户才能访问被视图保护装饰的视图函数

        ** 当为视图函数添加多个装饰器的时候，route装饰器应该位于最外层

        当未登录的用户访问需要登录才能请求的视图函数的时候，如果添加了login_required装饰器
        程序会自动重定向到登录页面，此时需要通过login_manager的login_view属性设置重定向的视图函数
        并且通过login_message_category设置提示消息的类别，login_message设置提示消息的内容
        具体见extensions文件

        在重定向的url中，会自动包含上一个页面的next参数，当登录了之后，会自动重定向到next参数指定的页面

        如果想为整个蓝图添加视图保护，可以使用请求钩子，添加login_required装饰器

        常见的响应状态码：
            200   成功
            201   请求成功，并且新建了资源
            204   请求成功，但是没有内容返回
            301   永久重定向
            302   临时重定向
            304   请求的内容没有修改，Not Modified 重定向到缓存
            404   请求的资源不存在
            400   请求参数不正确
            401   请求的用户没有认证
            403   请求的用户没有权限
            500   服务器内部错误
    :return:
    """
    form = SettingForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.blog_title = form.blog_title.data
        current_user.blog_sub_title = form.blog_sub_title.data
        current_user.about = form.about.data
        commit_data('add', current_user)
        flash('修改设置成功', 'success')
        return redirect(url_for('blog.index'))
    form.name.data = current_user.name
    form.blog_title.data = current_user.blog_title
    form.blog_sub_title.data = current_user.blog_sub_title
    form.about.data = current_user.about
    return render_template('admin/settings.html', form=form)


@admin_bp.route('/post/manage')
@login_required
@confirm_required
def manage_post():
    """
        文章管理页面
    :return:
    """

    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLUELOG_MANAGE_POST_PER_PAGE']

    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, per_page=per_page)

    posts = pagination.items

    return render_template('admin/manage_post.html', posts=posts, pagination=pagination, page=page)


@admin_bp.route('/post/new', methods=['GET', 'POST'])
@login_required
@confirm_required
def new_post():
    """
        添加文章页面
    :return:
    """
    form = PostForm()
    if form.validate_on_submit():
        """表单验证通过"""
        title = form.title.data
        body = form.body.data
        category = Category.query.get(form.category.data)
        # category_id = form.category.data  效果同上
        post = Post(title=title, body=body, category=category)
        db.session.add(post)
        db.session.commit()
        flash('保存成功', 'success')
        return redirect(url_for('blog.show_post', post_id=post.id))

    return render_template('admin/new_post.html', form=form)


@admin_bp.route('/new/category', methods=['GET', 'POST'])
@login_required
@confirm_required
def new_category():
    """
        新建文章分类
    :return:
    """

    form = CategoryForm()
    if form.validate_on_submit():
        """进行表单验证的时候，会自动查找当前的类中是否存在validate_字段名开头的属性
           如果存在的话，会在验证的时候，将这部分的数据也进行验证
        """
        name = form.name.data
        if Category.query.filter(Category.name == name).first():
            flash('当前分类已经存在，请勿重复添加', 'warning')
            return redirect_back()
        category = Category()
        category.name = name

        commit_data('add', category)
        flash('添加新分类成功！', 'success')
        return redirect(url_for('admin_bp.manage_category'))
    return render_template('admin/new_category.html', form=form)


@admin_bp.route('/new/link', methods=['GET', 'POST'])
@login_required
@confirm_required
def new_link():
    """
        新建链接
    :return:
    """
    form = LinkForm()
    link = Link()
    if form.validate_on_submit():
        link.name = form.name.data
        link.url = form.url.data
        commit_data('add', link)
        flash('新建链接成功', 'success')
        return redirect(url_for('admin_bp.manage_link'))

    return render_template('admin/new_link.html', form=form)


@admin_bp.route('/category/manage')
@login_required
@confirm_required
def manage_category():
    """
        管理分类
    :return:
    """
    return render_template('admin/manage_category.html')


@admin_bp.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@confirm_required
def edit_category(category_id):
    """
        编辑分类
    :param category_id:
    :return:
    """

    form = CategoryForm()
    category = Category.query.get(category_id)
    if form.validate_on_submit():
        category.name = form.name.data
        commit_data('add', category)
        flash('编辑成功', 'success')
        return redirect(url_for('admin_bp.manage_category'))

    return render_template('admin/edit_category.html', form=form)


@admin_bp.route('/category/<int:category_id>/delete', methods=['POST'])
@login_required
@confirm_required
def delete_category(category_id):
    """
        删除分类
    :param category_id:
    :return:
    """

    category = Category.query.get_or_404(category_id)

    if category.name == 'Default':
        flash('不允许删除默认的分类', 'warning')
        return redirect(url_for('admin_bp.manage_category'))

    category.delete()

    flash('删除该分类成功', 'success')

    return redirect(url_for('admin_bp.manage_category'))


@admin_bp.route('/comment/manage')
@login_required
@confirm_required
def manage_comment():
    """
        管理评论
    :return:
    """
    filter_ = request.args.get('filter', 'all')  # 获取评论页面的筛选规则
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLUELOG_COMMENT_PER_PAGE']
    if filter_ == 'admin':
        # 来自管理员的评论
        pagination = Comment.query.filter_by(from_admin=True).order_by(
            Comment.timestamp.desc()).paginate(page, per_page=per_page)

    elif filter_ == 'unread':
        # 未读评论
        pagination = Comment.query.filter_by(reviewed=False).order_by(
            Comment.timestamp.desc()).paginate(page, per_page=per_page)

    else:
        pagination = Comment.query.order_by(
            Comment.timestamp.desc()).paginate(page, per_page=per_page)  # 获取所有未审核评论

    comments = pagination.items

    return render_template(
        'admin/manage_comment.html', comments=comments,
        pagination=pagination)


@admin_bp.route('/link/manage')
@login_required
@confirm_required
def manage_link():
    """
        管理链接，这里的链接之所以能不传入模板
        是因为在模板上下文处理函数中默认传入模板中的
    :return:
    """
    return render_template('admin/manage_link.html')


@admin_bp.route('/link/<int:link_id>/edit', methods=['GET', 'POST'])
@login_required
@confirm_required
def edit_link(link_id):
    """
        编辑文章的链接
    :param link_id:
    :return:
    """
    form = LinkForm()
    link = Link.query.get_or_404(link_id, description='当前指定的链接不存在')
    if form.validate_on_submit():
        link.name = form.name.data
        link.url = form.url.data
        commit_data('add', link)
        flash('编辑成功', 'success')
        return redirect(url_for('admin_bp.manage_link'))
    form.name.data = link.name
    form.url.data = link.url
    return render_template('admin/edit_link.html', form=form)


@admin_bp.route('/link/<int:link_id>/delete', methods=['POST'])
@login_required
@confirm_required
def delete_link(link_id):
    """
        删除链接
    :param link_id:
    :return:
    """
    link = Link.query.get_or_404(link_id)
    commit_data('delete', link)
    flash('删除链接成功', 'success')
    return redirect(url_for('admin_bp.manage_link'))


@admin_bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
@confirm_required
def edit_post(post_id):
    """
        编辑文章
    :return:
    """
    post = Post.query.get_or_404(post_id)
    form = PostForm()
    # form.category.choices = [(i.id, i.name) for i in Category.query.order_by(
    #     Category.name).all()]  # 指定分类下拉选项的内容
    if form.validate_on_submit():
        """表单验证通过的逻辑"""
        post.title = form.title.data
        post.body = form.body.data
        post.category_id = form.category.data
        commit_data('add', post)
        flash('编辑文章成功！！', 'success')
        return redirect(url_for('blog.show_post', post_id=post.id))

    form.title.data = post.title  # 将文章的内容进行展示
    form.body.data = post.body
    form.category.data = post.category_id

    return render_template('admin/edit_post.html', form=form)


@admin_bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
@confirm_required
def delete_post(post_id):
    """
        删除文章
    :param post_id:
    :return:
    """

    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('删除成功！', 'success')
    return redirect_back()


@admin_bp.route('/set-comment/<int:post_id>', methods=['POST'])
@login_required
@confirm_required
def set_comment(post_id):
    """
        开启/关闭文章评论
    :param post_id: 文章id
    :return:
    """
    post = Post.query.get_or_404(post_id)
    if post.can_comment:
        post.can_comment = False
        flash('关闭评论成功', 'info')
    else:
        post.can_comment = True
        flash('开启评论成功！', 'info')

    db.session.commit()

    return redirect(url_for('blog.show_post', post_id=post.id))


@admin_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
@confirm_required
def delete_comment(comment_id):
    """
        删除评论
    :param comment_id:
    :return:
    """
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash('删除评论成功！！', 'success')
    return redirect_back()


@admin_bp.route('/comment/<int:comment_id>/approve', methods=['POST'])
@login_required
@confirm_required
def approve_comment(comment_id):
    """
        审核评论
    :param comment_id:
    :return:
    """

    comment = Comment.query.get_or_404(comment_id)
    comment.reviewed = True

    db.session.commit()
    flash('评论审核通过', 'success')

    return redirect_back()


@admin_bp.route('/files/<path:filename>')
@login_required
@confirm_required
def uploaded_files(filename):
    path = current_app.config['UPLOADED_PATH']
    return send_from_directory(path, filename)


@admin_bp.route('/upload', methods=['POST'])
@login_required
@confirm_required
def upload():
    """
        在集成富文本编辑器的时候，因为表单默认开启了CSRF保护，所以上传图片不会成功
        需要配置CKEDITOR_ENABLE_CSRF = True来关闭CSRF验证，导致的400错误
    :return:
    """
    file = request.files.get('upload')  # 获取上传的文件
    extension = file.filename.split('.')[1].lower()  # 获取扩展名
    if extension not in ['jpg', 'gif', 'png', 'jpeg']:  # 验证文件类型示例
        return upload_fail(message='只能上传图片！')
    file.save(os.path.join(current_app.config['UPLOADED_PATH'], file.filename))
    url = url_for('admin_bp.uploaded_files', filename=file.filename)
    return upload_success(url=url)


@admin_bp.route('/upload/avatar', methods=['GET', 'POST'])
@login_required
@confirm_required
def upload_avatar():
    form = UploadForm()

    if form.validate_on_submit():
        image = form.image.data
        filename = random_filename(image.filename)
        base_with = current_app.config['AVATARS_PHOTO_SIZE']
        new_image = resize_avatar(image, filename, base_with)  # 裁剪图片的尺寸
        new_image_s = resize_avatar(image, filename, 80)
        new_image_l = resize_avatar(image, filename, 110)
        user = current_user._get_current_object()  # 获取代理的真实用户对象
        user.avatar_s = new_image_s
        user.avatar_m = new_image
        user.avatar_l = new_image_l
        commit_data('add', user)
    return render_template('admin/upload_avatar.html', form=form)
