import time
from http import HTTPStatus

from mock import Mock
from micro_templating.auth import Authenticator
from micro_templating.error_messages import token_is_invalid_message, unbeary_auth_message, no_auth_header_message
from tests.conftest import NoAuthServerAuthenticator


class TestAuthenticator:

    def get_decorated_mock(self, authenticator: Authenticator):
        mock_function = Mock()
        decorated_function = authenticator.token_required(mock_function)
        return mock_function, decorated_function

    def test_missing_header(self, client, authenticator: Authenticator):

        with client.application.test_request_context():
            mock, decorated_mock = self.get_decorated_mock(authenticator)
            message, response_code = decorated_mock()

            assert response_code == HTTPStatus.UNAUTHORIZED
            assert message.json["message"] == no_auth_header_message
            assert not mock.called

    def test_no_bearer(self, client, authenticator: NoAuthServerAuthenticator):
        valid_token = authenticator.sign(issuer=f"{authenticator.auth_host}",
                                         audience=f"{authenticator.audience}",
                                         sub="someone")

        with client.application.test_request_context(headers={"Authorization": f"Basic {valid_token}"}):
            mock, decorated_mock = self.get_decorated_mock(authenticator)
            message, response_code = decorated_mock()

            assert response_code == HTTPStatus.UNAUTHORIZED
            assert message.json["message"] == unbeary_auth_message
            assert not mock.called

    def test_expired(self, client, authenticator: NoAuthServerAuthenticator):
        yesterday = int(time.time()) - 60*60*24
        token = authenticator.sign(issuer=f"{authenticator.auth_host}",
                                   audience=f"{authenticator.audience}",
                                   expires_at=yesterday,
                                   sub="someone")
        with client.application.test_request_context(headers={"Authorization": f"Bearer {token}"}):

            mock, decorated_mock = self.get_decorated_mock(authenticator)
            message, response_code = decorated_mock()

            assert response_code == HTTPStatus.UNAUTHORIZED
            assert message.json["message"] == token_is_invalid_message.format('Signature has expired.')

    def test_wrong_audience(self, client, authenticator: NoAuthServerAuthenticator):
        token = authenticator.sign(issuer=f"{authenticator.auth_host}",
                                   audience=f"{authenticator.audience}-bad",
                                   sub="someone")
        with client.application.test_request_context(headers={"Authorization": f"Bearer {token}"}):

            mock, decorated_mock = self.get_decorated_mock(authenticator)
            message, response_code = decorated_mock()

            assert response_code == HTTPStatus.UNAUTHORIZED
            assert message.json["message"] == token_is_invalid_message.format('Invalid audience')

    def test_wrong_iss(self, client, authenticator: NoAuthServerAuthenticator):
        token = authenticator.sign(issuer=f"{authenticator.auth_host}-bad",
                                   audience=f"{authenticator.audience}",
                                   sub="someone")

        with client.application.test_request_context(headers={"Authorization": f"Bearer {token}"}):

            mock, decorated_mock = self.get_decorated_mock(authenticator)
            message, response_code = decorated_mock()

            assert response_code == HTTPStatus.UNAUTHORIZED
            assert message.json["message"] == token_is_invalid_message.format('Invalid issuer')
            assert not mock.called

    def test_wrong_signature(self, client, authenticator: NoAuthServerAuthenticator):
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        token = authenticator.sign(issuer=f"{authenticator.auth_host}",
                                   audience=f"{authenticator.audience}",
                                   sub="someone", key=pem)

        with client.application.test_request_context(headers={"Authorization": f"Bearer {token}"}):

            mock, decorated_mock = self.get_decorated_mock(authenticator)
            message, response_code = decorated_mock()

            assert response_code == HTTPStatus.UNAUTHORIZED
            assert message.json["message"] == token_is_invalid_message.format("Signature verification failed.")
            assert not mock.called

    def test_ok(self, client, authenticator: NoAuthServerAuthenticator):
        token = authenticator.sign(issuer=f"{authenticator.auth_host}",
                                   audience=f"{authenticator.audience}",
                                   sub="someone")

        with client.application.test_request_context(headers={"Authorization": f"Bearer {token}"}):

            mock, decorated_mock = self.get_decorated_mock(authenticator)
            decorated_mock()

            assert mock.called
