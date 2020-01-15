from http import HTTPStatus

from mock import Mock

from auth import Authenticator
from tests.conftest import NoAuthServerAuthenticator


class TestAuthenticator:

    def get_decorated_mock(self, authenticator: Authenticator):
        mock_function = Mock()
        decorated_function = authenticator.token_required(mock_function)
        return mock_function, decorated_function

    def test_missing_token(self, client, authenticator: Authenticator):

        with client.application.test_request_context():
            mock, decorated_mock = self.get_decorated_mock(authenticator)
            message, response_code = decorated_mock()

            assert response_code == HTTPStatus.UNAUTHORIZED
            assert not mock.called

    def test_wrong_audience(self, client, authenticator: NoAuthServerAuthenticator):
        token = authenticator.sign(issuer=f"{authenticator.auth_host}",
                                   audience=f"{authenticator.audience}-bad",
                                   sub="someone")
        with client.application.test_request_context(headers={"Authorization": f"Bearer {token}"}):

            authenticator.verify(token)
            mock, decorated_mock = self.get_decorated_mock(authenticator)
            message, response_code = decorated_mock()

            assert response_code == HTTPStatus.UNAUTHORIZED
            assert message.json["message"] == 'Token is invalid: Invalid audience'

    def test_wrong_iss(self, client, authenticator: NoAuthServerAuthenticator):
        token = authenticator.sign(issuer=f"{authenticator.auth_host}-bad",
                                   audience=f"{authenticator.audience}",
                                   sub="someone")

        with client.application.test_request_context(headers={"Authorization": f"Bearer {token}"}):

            authenticator.verify(token)
            mock, decorated_mock = self.get_decorated_mock(authenticator)
            message, response_code = decorated_mock()

            assert response_code == HTTPStatus.UNAUTHORIZED
            assert message.json["message"] == 'Token is invalid: Invalid issuer'
