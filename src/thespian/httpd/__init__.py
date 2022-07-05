from dataclasses import dataclass

from flask import Flask, redirect, render_template


@dataclass
class Server:
    data: dict
    port: int = 5000

    @classmethod
    def run(cls, content: dict, port: int) -> None:
        server = cls(content, port)
        webapp = Flask(__name__)

        @webapp.route("/")
        def index():
            return redirect("/character")

        @webapp.route("/character")
        def character():
            return render_template("index.html", **server.data)

        webapp.run(port=server.port)
