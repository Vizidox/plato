"""Module containing any function or class regarding authentication
"""
from abc import ABC, abstractmethod
from functools import wraps
from typing import Callable, TypeVar, Any, cast
from .error_messages import unbeary_auth_message, no_auth_header_message, token_is_invalid_message
import requests
from flask import request, jsonify, g
from jose import jwt, JWTError

FuncType = Callable[..., Any]
F = TypeVar('F', bound=FuncType)


class Authenticator(ABC):
    """
    Authenticator is the abstract class responsible for cross-checking any information regarding the bearer token.
    """

    @abstractmethod
    def token_required(self, f: Callable) -> F:
        """
        Validates token to access the decorated resource
        Args:
            f: the method to be decorated
        Returns:
            F: the decorated method
        """
        ...


class FlaskAuthenticator(Authenticator):
    """
    The Authenticator to be used with Flask.
    Currently coupled to our Authentication provider, Keycloak.

    Attributes:
        auth_host: URL representing the keycloak realm, e.g http://localhost:8080/auth/realms/example_realm
        auth_host_origin: URL keycloak signs with, defaults to auth_host
        oauth_config_url: URL for OIDC well known resources on server
        audience: Audience used for JWT validation

    """

    def __init__(self, auth_host: str, audience: str, auth_host_origin: str = ""):
        self.auth_host = auth_host
        self.auth_host_origin = auth_host_origin if auth_host_origin else auth_host
        self.oauth_config_url = f"{auth_host}/.well-known/openid-configuration"
        self._oauth_config = None
        self._jwks = None
        self.audience = audience

    @property
    def oauth_config(self):
        """
        Obtains the OAuth config making a request to self.oauth_config_url and stores it at self.oauth_config

        """
        if self._oauth_config is None:
            self._oauth_config = requests.get(self.oauth_config_url).json()
        return self._oauth_config

    @property
    def jwks(self):
        """
        Obtains the JSON web keys making a request dependant on the oauth_config and stores them at self._jwks_json

        """
        if self._jwks is None:
            _jwks_json = requests.get(self.oauth_config['jwks_uri']).json()
            self._jwks = {key_data['kid']: key_data for key_data in _jwks_json['keys']}
        return self._jwks

    def token_required(self, f: Callable) -> F:
        """
        Retrieves most recent JWKs from the OAUTH configuration and sets up the wrapper for JWT validation
        Args:
            f: decorated function

        """

        @wraps(f)
        def decorated(*args, **kwargs):
            """
            Uses the JWKs to validate a JWT token included in the request, adding the account id as the first argument.
            Args:
                *args: decorated function's arguments
                **kwargs: decorated function's keyword arguments

            Returns:

            """
            header = request.headers.get('Authorization', None)

            if header is None:
                return jsonify({'message': no_auth_header_message}), 401

            if not header.startswith(("Bearer ", "bearer ")):
                return jsonify({'message': unbeary_auth_message}), 401

            token = header[7:]

            try:
                unverified_header = jwt.get_unverified_header(token)
                unverified_key_id = unverified_header['kid']
                key = self.jwks[unverified_key_id]

                verified_token = jwt.decode(token=token,
                                            key=key,
                                            algorithms=key['alg'],
                                            issuer=self.auth_host_origin,
                                            audience=self.audience,
                                            options={
                                                    'require_aud': True,
                                                    'require_iat': True,
                                                    'require_iss': True,
                                                    'require_exp': True,
                                                    'require_sub': True
                                                }
                                            )
                g.auth_id = verified_token['sub']
                g.partner_id = verified_token['clientId']
                return f(*args, **kwargs)

            except JWTError as e:
                return jsonify({'message': token_is_invalid_message.format(e)}), 401

        return cast(F, decorated)
