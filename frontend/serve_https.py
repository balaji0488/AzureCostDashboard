import os
from werkzeug.serving import run_simple
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.wrappers import Request, Response

# Path to the mkdocs built site
site_dir = os.path.join(os.path.dirname(__file__), 'site')

import urllib.request
from werkzeug.wrappers import Request, Response

def application(environ, start_response):
    request = Request(environ)
    
    # Proxy /api requests to the local backend to avoid Mixed Content (HTTPS -> HTTP) and CORS issues
    if request.path.startswith('/api/'):
        target_url = f"http://localhost:7071{request.path}"
        if request.query_string:
            target_url += f"?{request.query_string.decode('utf-8')}"
            
        # Forward the headers, particularly the Authorization Bearer token
        headers = {k: v for k, v in request.headers.items() if k.lower() not in ('host', 'content-length')}
        req = urllib.request.Request(target_url, headers=headers)
        
        try:
            with urllib.request.urlopen(req) as resp:
                body = resp.read()
                proxy_response = Response(body, status=resp.getcode())
                for k, v in resp.headers.items():
                    if k.lower() not in ('transfer-encoding', 'connection', 'content-length', 'content-encoding', 'keep-alive', 'server'):
                        proxy_response.headers[k] = v
                return proxy_response(environ, start_response)
        except urllib.error.HTTPError as e:
            proxy_response = Response(e.read(), status=e.code)
            for k, v in e.headers.items():
                if k.lower() not in ('transfer-encoding', 'connection', 'content-length', 'content-encoding', 'keep-alive', 'server'):
                    proxy_response.headers[k] = v
            return proxy_response(environ, start_response)
        except Exception as e:
            proxy_response = Response(f"Backend proxy error: {str(e)}", status=502)
            return proxy_response(environ, start_response)

    response = Response('Not Found', status=404)
    return response(environ, start_response)

# Serve static files from the MkDocs 'site' directory
app = SharedDataMiddleware(application, {
    '/': site_dir
})

# Middleware to rewrite '/' to '/index.html'
class IndexRewriteMiddleware(object):
    def __init__(self, app):
        self.app = app
    def __call__(self, environ, start_response):
        if environ.get('PATH_INFO', '') == '/':
            environ['PATH_INFO'] = '/index.html'
        return self.app(environ, start_response)

secure_app = IndexRewriteMiddleware(app)

if __name__ == '__main__':
    print("-------------------------------------------------------")
    print("Serving Securely on https://localhost:8000")
    print("Make sure you run 'mkdocs build' first whenever you make changes!")
    print("-------------------------------------------------------")
    run_simple('localhost', 8000, secure_app, ssl_context='adhoc', threaded=True)
