from flask import Flask
from flask.cli import with_appcontext

from .db import db
from .db.models import Template


def register_cli_commands(app: Flask):
    @app.shell_context_processor
    def make_shell_context():
        return dict(app=app, db=db, Template=Template)

    @app.cli.command("get_templates")
    @with_appcontext
    def get_templates():
        print(Template.query.all())
