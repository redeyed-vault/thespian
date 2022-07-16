from dataclasses import dataclass

from flask import Flask, redirect, render_template


@dataclass
class Server:
    data: dict

    @classmethod
    def run(cls, content: dict) -> None:
        server = cls(content)
        webapp = Flask(__name__)

        @webapp.route("/")
        def index():
            return redirect("/character")

        @webapp.route("/character")
        def character():
            return render_template("index.html", **server.data)

        webapp.run()
