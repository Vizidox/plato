# -*- coding: utf-8 -*-
"""database.py
Methods for interacting with the database.
"""
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker

from .models import *


def init_db(engine: Engine) -> scoped_session:
    """

    Initializes database by setting up the scope session to be used
     in the models and returning it to use where relevant.

    Args:
        engine (Engine): Database engine to be initialized when using the application either through Flask or a bin.
    Returns:
        scoped_session: The local thread-safe session
    """
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))
    Base.query = db_session.query_property()
    Base.metadata.create_all(bind=engine)

    return db_session
