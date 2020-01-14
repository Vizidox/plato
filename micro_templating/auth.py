"""Module containing any function or class regarding authentication
"""
from functools import wraps
from typing import Dict

import requests
from flask import request, jsonify, g
from jose import jwt, JWTError


class Authenticator:
    """
    Authenticator is the class responsible for cross-checking any information regarding the bearer token.
    Currently coupled to our Authentication provider, Keycloak.

    Attributes:
        auth_host: URL representing the keycloak realm, e.g http://localhost:8080/auth/realms/example_realm
        oauth_config_url: URL for OIDC well known resources on server
        oauth_config: JSON response for well known server resources
        audience: Audience used for JWT validation
    """

    def __init__(self, auth_host: str, audience: str):
        self.auth_host = auth_host
        self.oauth_config_url = f"{auth_host}/.well-known/openid-configuration"
        self.oauth_config = requests.get(self.oauth_config_url).json()
        self.audience = audience

    def token_required(self, f):
        """
        Retrieves most recent JWKs from the OAUTH configuration and sets up the wrapper for JWT validation
        Args:
            f: decorated function

        Returns:

        """
        _jwks_json = requests.get(self.oauth_config['jwks_uri']).json()
        jwks: Dict[str, Dict] = {key_data['kid']: key_data for key_data in _jwks_json['keys']}

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

            token = header[7:] if header is not None and header.startswith(("Bearer ", "bearer ")) else None

            if not token:
                return jsonify({'message': 'Token is missing!'}), 401

            try:
                unverified_header = jwt.get_unverified_header(token)
                unverified_key_id = unverified_header['kid']
                key = jwks[unverified_key_id]

                verified_token = jwt.decode(token=token,
                                            key=key,
                                            algorithms=key['alg'],
                                            issuer=self.auth_host,
                                            audience=self.audience
                                            )
                g.auth_id = verified_token['sub']
                return f(*args, **kwargs)

            except JWTError as e:
                return jsonify({'message': f'Token is invalid: {e}'}), 401

        return decorated
