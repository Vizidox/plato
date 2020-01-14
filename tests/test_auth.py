from http import HTTPStatus

from mock import Mock


def test_missing_token(client, authenticator):

    with client.application.test_request_context():
        mock_function = Mock()
        decorated_function = authenticator.token_required(mock_function)
        message, response_code = decorated_function()

        assert response_code == HTTPStatus.UNAUTHORIZED

        assert not mock_function.called




