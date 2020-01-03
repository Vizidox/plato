from functools import wraps
from typing import Dict

import requests
from flask import request, jsonify, g
from jose import jwt, JWTError
from settings import AUTH_SERVER, CLIENT_ID

oauth_config = requests.get(f"{AUTH_SERVER}/.well-known/openid-configuration").json()


def token_required(f):
    """
    Retrieves most recent JWKs from the OAUTH configuration and sets up the wrapper for JWT validation
    Args:
        f: decorated function

    Returns:

    """
    _jwks_json = requests.get(oauth_config['jwks_uri']).json()
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
                                        issuer=AUTH_SERVER,
                                        audience=CLIENT_ID
                                        )
            g.auth_id = verified_token['sub']
            return f(*args, **kwargs)

        except JWTError as e:
            return jsonify({'message': f'Token is invalid: {e}'}), 401

    return decorated
