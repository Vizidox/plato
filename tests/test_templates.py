from tests.conftest import MockAuthenticator


class TestTemplates:

    GET_TEMPLATES_ENDPOINT = '/templates/'
    GET_TEMPLATES_METHOD_NAME = "templates"

    def test_auth_protected(self, authenticator: MockAuthenticator):
        assert self.GET_TEMPLATES_METHOD_NAME in authenticator.authenticated_endpoints

