from typing import Optional

import click
from flask import Flask
from flask.cli import with_appcontext
import json
from .db import db
from .db.models import Template


def register_cli_commands(app: Flask):
    @app.shell_context_processor
    def make_shell_context():
        return dict(app=app, db=db, Template=Template)

    @app.cli.command("register_new_template")
    @click.argument("partner_id", type=click.STRING)
    @click.argument("json_file", type=click.File("r"))
    @with_appcontext
    def register_new_template(partner_id: str, json_file):
        """
        Imports new template from json file and inserts it in database
        Args:
            partner_id: partner owning said template
            json_file: file containing the template json
        """
        template_entry_json = json.load(json_file)
        new_template = Template.from_json_dict(partner_id, template_entry_json)
        db.session.add(new_template)
        db.session.commit()

    @app.cli.command("export_template")
    @click.argument("partner_id", type=click.STRING)
    @click.argument("output", type=click.File("w"))
    @click.option("--template-id", default=None, type=click.STRING)
    @with_appcontext
    def export_template(partner_id: str, output, template_id: Optional[str]):
        """
        Export new template to file
        Args:
            partner_id: partner who owns the credential
            output: output file
            template_id: template to be exported
        """
        if template_id is None:
            templates = Template.query.filter_by(partner_id=partner_id)
            template_options = "\n".join([template.id for template in templates])
            click.echo(template_options)
            template_id = click.prompt("Please enter the id for the template you wish to export")
        template = Template.query.filter_by(partner_id=partner_id, id=template_id).one()
        json.dump(template.json_dict(), output)
