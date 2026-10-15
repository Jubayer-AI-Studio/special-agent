import os
import sys
from urllib.parse import parse_qs, urlencode

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.web_server import app as fastapi_app

class VercelPathRewriteMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            qs = scope.get("query_string", b"").decode("utf-8")
            params = parse_qs(qs, keep_blank_values=True)
            if "__path__" in params:
                subpath = params.pop("__path__")[0].lstrip("/")
                scope["path"] = "/api/" + subpath
                new_q = [(k, v) for k, vals in params.items() for v in vals]
                scope["query_string"] = urlencode(new_q).encode("utf-8")
        await self.inner(scope, receive, send)

app = VercelPathRewriteMiddleware(fastapi_app)
