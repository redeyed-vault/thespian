from dataclasses import dataclass

from flask import Flask, redirect, render_template


@dataclass
class Server:
    data: dict
    port: int = 5000

    def __enter__(self):
        return self

    def __exit__(self, exec_type, value, tb) -> None:
        pass

    def run(self) -> None:
        webapp = Flask(__name__)

        @webapp.route("/")
        def index():
            return redirect("/character")

        @webapp.route("/character")
        def character():
            return render_template("index.html", **self.data)

        webapp.run(port=self.port)
