from contextlib import contextmanager
from flask import appcontext_pushed, g


@contextmanager
def partner_id_set(app):
    """
    Sets partner_id in g as a context
    Args:
        app:
    """

    def handler(sender, **kwargs):
        pass

    with appcontext_pushed.connected_to(handler, app):
        yield


def get_message(response):
    return response.json["message"]
