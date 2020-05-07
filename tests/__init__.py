from contextlib import contextmanager
from flask import appcontext_pushed, g

@contextmanager
def partner_id_set(app, partner_id):
    """
    Sets partner_id in g as a context
    Args:
        app:
        partner_id:
    """
    def handler(sender, **kwargs):
        g.partner_id = partner_id
    with appcontext_pushed.connected_to(handler, app):
        yield


def get_message(response):
    return response.json["message"]
