from flask import render_template, Response


def index() -> Response:
    return render_template("pages/index.html")


def privacy() -> Response:
    return render_template("pages/privacy.html")


def tos() -> Response:
    return render_template("pages/tos.html")
