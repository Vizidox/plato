from typing import Union, List, Iterable, Dict, Any


def get_unverified_header(token: str) -> Dict[Any, Any]: ...
def decode(token: str,
           key: Union[str, Dict[str, str]],
           *,
           algorithms: Union[str, List[str]] = ...,
           audience: str = ...,
           issuer: Union[str, Iterable[str]] = ...,
           subject: str = ...,
           access_token: str = ...) -> Dict[Any, Any]: ...

class JOSEError(Exception): pass
class JWTError(JOSEError): pass
class ExpiredSignatureError(JWTError): pass
class JWTClaimsError(JWTError): pass
