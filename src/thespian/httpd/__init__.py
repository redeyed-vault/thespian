from dataclasses import dataclass
import os

from aiohttp import web
import aiohttp_jinja2
import jinja2


@dataclass
class Server:
    data: dict
    port: int = 5000

    def __enter__(self):
        return self

    def __exit__(self, exec_type, value, tb) -> None:
        pass

    def run(self) -> None:
        routes = web.RouteTableDef()
        routes.static("/css", "src/thespian/httpd/css/")

        @routes.get("/")
        @aiohttp_jinja2.template("index.html")
        async def index(request: web.Request):
            return self.data

        app = web.Application()
        app.add_routes(routes)
        aiohttp_jinja2.setup(
            app,
            loader=jinja2.FileSystemLoader(
                os.path.join(os.path.dirname(__file__), "templates")
            ),
        )
        web.run_app(app, host="127.0.0.1", port=self.port)
