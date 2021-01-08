# -*- coding: utf-8 -*-
"""Database models

All the classes in this module represent the database objects present in the microservice and extend a declarative
base from sqlalchemy.

"""
from typing import Sequence, List

from plato.db import db
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB, ENUM, ARRAY


class Template(db.Model):
    """
    Database model for a Template

    The unique identifier for the table is `id`.
    The metadata has some optional but relevant entries:
        qr_entries
            This is an array of JMESPath friendly sequences to represent where in the schema
            are the urls to be transformed into QR codes.

            Examples
                "course.organization.contact.website_url"

    Attributes:
        id (str): The id for the template
        schema (dict): JSON dictionary with jsonschema used for validation in said template
        type (str): MIME type for template type, currently restricted to 'text/html'
        metadata_ (dict): JSON dictionary for arbitrary data useful for owner
    """
    __tablename__ = "template"
    id = db.Column(String, primary_key=True)
    schema = db.Column(JSONB, nullable=False)
    type = db.Column(ENUM("text/html", name="template_mime_type"), nullable=False)
    metadata_ = db.Column(JSONB, name="metadata", nullable=True)
    example_composition = db.Column(JSONB, nullable=False)
    tags = db.Column(ARRAY(String), name="tags", nullable=False, server_default="{}")

    def __init__(self, id_: str, schema: dict, type_: str,
                 metadata: dict,
                 example_composition: dict,
                 tags: Sequence[str]):
        self.id = id_
        self.schema = schema
        self.type = type_
        self.metadata_ = metadata
        self.example_composition = example_composition
        self.tags = tags

    @classmethod
    def from_json_dict(cls, json_: dict) -> 'Template':
        """
        Builds a model from a dictionary that follows the export standard.

        Args:
            json_: dict with template details.

        Returns:
            Template
        """

        return Template(id_=json_["title"],
                        schema=json_["schema"],
                        type_=json_["type"],
                        metadata=json_["metadata"],
                        example_composition=json_["example_composition"],
                        tags=json_["tags"])

    def update_from_json_dict(self, json_: dict) -> None:
        """
        Updates a template object from a dictionary that follows the export standard.

        Args:
            json_: dict with template details.
        """
        self.schema = json_["schema"]
        self.type = json_["type"]
        self.metadata_ = json_["metadata"]
        self.example_composition = json_["example_composition"]
        self.tags = json_["tags"]

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
        json_["example_composition"] = self.example_composition
        json_["tags"] = self.tags
        return json_

    def get_qr_entries(self) -> List[str]:
        """
        Fetches all the qr_entries for the template as a list comprised of JMESPath friendly strings
        Returns:
            List[str]
        """
        return self.metadata_.get("qr_entries", [])

    def __repr__(self):
        return '<Template %r>' % self.id
