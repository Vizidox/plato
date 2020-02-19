# -*- coding: utf-8 -*-
"""Database models

All the classes in this module represent the database objects present in the microservice and extend a declarative
base from sqlalchemy.

"""
from micro_templating.db import db
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB, ENUM


class Template(db.Model):
    """
    Database model for a Template

    The unique identifiers for the table are `auth_id` and `id`.

    Attributes:
        auth_id (str): The id for the owner of the template
        id (str): The id for the template
        schema (dict): JSON dictionary with jsonschema used for validation in said template
        type (str): MIME type for template type, currently restricted to 'text/html'
        metadata_ (dict): JSON dictionary for arbitrary data useful for owner
    """
    __tablename__ = "template"
    partner_id = db.Column(String, primary_key=True)
    id = db.Column(String, primary_key=True)
    schema = db.Column(JSONB, nullable=False)
    type = db.Column(ENUM("text/html", name="template_mime_type"), nullable=False)
    metadata_ = db.Column(JSONB, name="metadata", nullable=True)

    def __init__(self, partner_id, id_: str, schema: dict, type_: str, metadata: dict):
        self.partner_id = partner_id
        self.id = id_
        self.schema = schema
        self.type = type_
        self.metadata_ = metadata

    def __repr__(self):
        return '<Template %r - %r>' % (self.partner_id, self.id)
