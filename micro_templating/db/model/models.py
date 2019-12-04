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
