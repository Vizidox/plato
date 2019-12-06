from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Template(Base):
    __tablename__ = "template"
    auth_id = Column(String, primary_key=True)
    id = Column(String, primary_key=True)
    schema = Column(JSONB, nullable=False)
    type = Column(ENUM("text/html"), nullable=False)
    metadata = Column(JSONB, nullable=True)

    def __init__(self, auth_id, id_: str, schema: dict, type_: str, metadata: dict):
        self.auth_id = auth_id
        self.id = id_
        self.schema = schema
        self.type = type_
        self.metadata = metadata

    def __repr__(self):
        return '<Template %r - %r>' % (self.auth_id, self.id)