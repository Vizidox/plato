from functools import wraps
from typing import Dict

import requests
from flask import request, jsonify
from jose import jwt, JWTError
from settings import AUTH_SERVER, CLIENT_ID

oauth_config = requests.get(f"{AUTH_SERVER}/.well-known/openid-configuration").json()


def token_required(f):

    _jwks_json = requests.get(oauth_config['jwks_uri']).json()
    jwks: Dict[str, Dict] = {key_data['kid']: key_data for key_data in _jwks_json['keys']}

    @wraps(f)
    def decorated(*args, **kwargs):
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

            return f(verified_token['sub'], *args, **kwargs)

        except JWTError as e:
            return jsonify({'message': f'Token is invalid: {e}'}), 401

    return decorated
