from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker

from .model import *


def init_db(engine: Engine) -> scoped_session:
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))
    Base.query = db_session.query_property()
    Base.metadata.create_all(bind=engine)

    return db_session
