## <center>Flask原理

### 本地上下文
	1. 设计原理：
		1. 每个视图函数都需要获取当前的请求对象和一些其他的变量
		   如果将请求对象当作参数，传入到视图函数中，会导致代码冗余，并且不易于维护
		   Flask考虑将这些变量设置为全局变量，但是相对于多线程来讲，会存在线程安全(多线程之间共享进程的资源，可能会导致全局变量被修改)
		   最后使用本地化线程来解决这个问题
	   2. 本地化线程的实质：
	   		全局变量，根据线程的ID进行数据存储，使用了Werkzeug.local.Local()，其中对greenlet协程的支持
	   		
	   		源码：
	   		    __slots__ 限制实例对象的属性, 不在元祖中的属性是不可读的
	   3. 中间件
	        1。 wsgi允许使用中间件来包装程序，为程序在被调用之前添加额外的设置和功能
	        当请求被发送过来的时候，会首先调用包装在可调用对象外层的中间件，
	        2.  实现了wsgi协议的服务器，在请求进入的时候，会首先调用可调用的对象
	            可调用的对象必须接受两个参数，分别是environ(包含了解析之后
	            请求的所有信息的字典)和start_response(需要在可调用对象中
	            调用的函数，用来发起响应)
	            `python`
	                from wsgiref.simple_server import make_server


    def hello(environ, start_response):
        status = '200 OK'
        response_headers = [('Content-type', 'text/html')]
        start_response(status, response_headers)
        return [b'<h1>Hello</h1>']


    class MyMiddleWare(object):

        def __init__(self, app):
            self.app = app

        def __call__(self, environ, start_response):
    
            def custom_start_response(status, headers, exc_info=None):
                headers.append(('A-CUSTOM-HEADER', 'Nothing'))
                return start_response(status, headers)

        return self.app(environ, custom_start_response)
        wrapped_app = MyMiddleWare(hello)
        server = make_server('localhost', 5600, wrapped_app)
        server.serve_forever()
        
   #
             3. 中间件接受可调用对象作为参数，这个可调用对象可以是其他中间件包装的可调用
                对象，中间件可以层层叠加，形成一个中间件堆栈，最后才会调用到实际的可调用对象
             4。 使用类定义的中间件必须实现__call__方法，接受environ和start_response作为参数
                最后调用传入的可调用对象，并且传递这两个参数
             5. 如果我们自己实现了中间件，最好的办法是嵌套在app.wsgi_app上
       4。 工作流程
            1.  请求响应循环
                1.  运行flask程序
                    两种方式： flask run 命令行的方式   app.run(过时)
                    flask run 调用的是cli.run_command()函数
                    但是最后调用的都是run_simple()函数(werkzeug.serving模块中)
                    run_simple函数中使用了两个中间件，分别是debug调试和提供静态文件
                    服务的中间件
                    最后，run_simple方法会调用inner()方法，inner方法是创建一个开发服务器
                2.  请求进入处理
                    1.  Flask类实现了__call__方法，当程序实例被调用的时候会执行__call__()方法
                        里面的内容，__call__()内部调用了wsgi_app()方法
                        
                        wsgi_app()相当于中间件，尝试获取响应，并且完成请求的分发
                        full_dispatch_request()尝试获取响应，完成完整的请求调度，process_request
                        方法对请求进行预处理，这回执行所有使用before_request请求钩子注册的函数             
              