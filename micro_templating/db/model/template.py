import sqlalchemy

from sqlalchemy import Table, Column, Integer, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from micro_templating.db.model import Base


class Template(Base):
    __tablename__ = "template"
    auth_id = Column(String, primary_key=True)
    id = Column(String, primary_key=True)
    schema = Column(JSONB, nullable=False)
    type = Column(ENUM("text/html"), nullable=False)
    metadata = Column(JSONB, nullable=True)
