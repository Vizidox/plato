# -*- coding: utf-8 -*-
"""Database models

All the classes in this module represent the database objects present in the microservice and extend a declarative
base from sqlalchemy.

"""
from typing import Sequence

from micro_templating.db import db
from sqlalchemy import String, ARRAY
from sqlalchemy.dialects.postgresql import JSONB, ENUM


class Template(db.Model):
    """
    Database model for a Template

    The unique identifiers for the table are `partner_id` and `id`.
    The metadata has some optional but relevant entries:
        qr_entries
            This is an array of JMESPath friendly sequences to represent where in the schema
            are the urls to be transformed into QR codes.

            Examples
                "course.organization.contact.website_url"

    Attributes:
        partner_id (str): The id for the owner of the template
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
    tags = db.Column(ARRAY(String), name="tags", nullable=False, server_default="{}")

    def __init__(self, partner_id, id_: str, schema: dict, type_: str, metadata: dict, tags: Sequence[str]):
        self.partner_id = partner_id
        self.id = id_
        self.schema = schema
        self.type = type_
        self.metadata_ = metadata
        self.tags = tags

    @classmethod
    def from_json_dict(cls, partner_id: str, json_: dict) -> 'Template':
        """
        Builds a model from a dictionary that follows the export standard.

        Args:
            partner_id: Id for the partner
            json_: dict with title, schema, and metadata entries.

        Returns:
            Template
        """
        template_id = json_["title"]
        schema = json_["schema"]
        type_ = json_["type"]
        metadata = json_["metadata"]
        tags = json_["tags"]

        return Template(partner_id=partner_id,
                        id_=template_id,
                        schema=schema,
                        type_=type_,
                        metadata=metadata,
                        tags=tags)

    def json_dict(self) -> dict:
        """
        Exports template data as dict.

        Returns:
            dict
        """
        json_ = dict()
        json_["title"] = self.id
        json_["schema"] = self.schema
        json_["type"] = self.type
        json_["metadata"] = self.metadata_
        json_["tags"] = self.tags
        return json_

    def get_qr_entries(self):
        """
        Fetches all the qr_entries for the template as a list comprised of JMESPath friendly strings
        Returns:
            List[str]
        """
        return self.metadata_.get("qr_entries", [])

    def __repr__(self):
        return '<Template %r - %r>' % (self.partner_id, self.id)
