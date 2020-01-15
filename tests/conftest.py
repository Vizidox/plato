from contextlib import nullcontext

import pytest
import requests
from jose import jwk, jwt, jws
from testcontainers.compose import DockerCompose
from testcontainers.core.utils import inside_container
from testcontainers.core.waiting_utils import wait_for

from auth import Authenticator
from micro_templating.flask_app import create_app, create_template_environment
from settings import PROJECT_NAME, PROJECT_VERSION

TEST_AUTH_HOST = f"http://{'auth:8080' if inside_container() else 'localhost:8788'}/auth/realms/micro-keycloak"
TEST_DB_URL = f"postgresql://test:test@{'database:5432' if inside_container() else 'localhost:5456'}/test"
TEST_OAUTH2_AUDIENCE = "content-provider"


class NoAuthServerAuthenticator(Authenticator):
        rsa_private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAlnSU24BTKsrI1aZRZAuK0jfPOmW6gVl5re9M8QrnEORlJLRW
quehKo+sYE0W4ZAJ9jht1bp0dIKRHIyNUfZAn9O3AZBuuo9r9D0Ya6TVySOMORZE
2pu5MA8l8lm5WAsbxaGDMD7CN+wQ+z4NpZy+sNNgaD3NhnYtmquxb+gcg8Rj0UHT
OYggjGQQSxGxy4MbJNBzNUeZH/dKHQ3Y+Vgl7D8x6XGfDwJIPkfXkYMjD0NZVL3J
O/IWicYF/FJI17EnDt//7CicldgsckDTjKaewetz7mG/rMIpofJFkoGbU0bBreu0
DRztkoo+urP9szO8VlsjG1nBRqVelYBdM6MGjQIDAQABAoIBAAWaAZDKjk4hjqil
sJIQ+/Inscdy0ibOtgELz8mJpmCyoDFlpXRne1CiWMCdHiT3v+cy4qP6dSuBUPXH
JdvPV0icEUw1nGnFvTcyrx4S3QLIGAhoE9gvxA1OAxOq04O7piUNhlzdeU2rtFYm
UUvBMjhTJlu7MVO4QqpniguokKc3MdZXpgcKkHwlx3HXom5X6Xdju8G4/TwjAFdQ
EPjp7d975achWIFrnUJHB1Ck9E78pewRnS8HhcIOvqL5QGHsEiEmtPxAJ/gy+Xna
jMThfSDQo0EWoaG27JihnakiNWjucNG042blvv2qtMab42myZn9tw3jtkAaAyKNH
iPGtZQECgYEA5Qiua5I4Lufr563UYZ/zeYTRqEf8taZqcYbfUy94H7Mh0MbaS4TI
oYthxIcf2E07b61MI/UyeOLiL955lqkpS99WKIVIuyN22utpoODakH7MDZ62jVtp
zp86/QeU4ymwi1kFvCXipTHgHqaaw3dgwQCFOFQ+WOVvTVbGEpO5IikCgYEAqCt2
aKFf8PAxRt7OEkVVvI6psFW2bxuE0nfsLzu4s9GwkKj9w7jL1exdGBxnzvX4Shp7
lhnE/SvfkRwt9P8PZ6XMWFm+tBW+T1dqOkjv783ZTqDjJbD42PV5WeFkDx/zMh6U
2vfk5CM24P1d13HFiCc5fqO++taibtNGBNT3dcUCgYEAtqxA6X1bIFZMOqHThfXc
bKy5x916uqs7tMac8q0mwynNq8YesCL9HpOb6/LWPGAFKuJumzNjCTX0r7djBP5w
+JnuDy2XP+NeVedzfSQ6TwtC1w4ijgY+EtW/Z7cXUkObEtlzEIirB5ULK4c4YvSh
D+7JUo8mlyKProCqRIDcJVkCgYAZ6Wh7QrI3u6q8EsSJyCknvoui4fIUOJdEnrnD
pV4WRu7/uyouqCCwO5U0i9vq5bd2I5J7VEkoAUSXZVInd8112PQdgOaDdP43125E
wMxHlN4w4VVej2AofdpO4Q27zt54EII7Iwsfo9Vm4WM+OQeIrRKM0soweDXbAa6+
O9pNSQKBgHE21ndCEikWO/k4bR1yh9zU1twQYRPtWZc2VkjKfWzWIy7vf93BIy/0
ZQlDIIhev43wFOBQOcKcw/6CSgRV4UhGzqLv5d6Twon1aopwPfHp7Pza9IaeTtXt
uRhTFpzJLFYdKjgUUj0ncsN8gDSa9jeuAqVRZ8ki7UsQ90WitiCG
-----END RSA PRIVATE KEY-----"""

        rsa_public_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAlnSU24BTKsrI1aZRZAuK
0jfPOmW6gVl5re9M8QrnEORlJLRWquehKo+sYE0W4ZAJ9jht1bp0dIKRHIyNUfZA
n9O3AZBuuo9r9D0Ya6TVySOMORZE2pu5MA8l8lm5WAsbxaGDMD7CN+wQ+z4NpZy+
sNNgaD3NhnYtmquxb+gcg8Rj0UHTOYggjGQQSxGxy4MbJNBzNUeZH/dKHQ3Y+Vgl
7D8x6XGfDwJIPkfXkYMjD0NZVL3JO/IWicYF/FJI17EnDt//7CicldgsckDTjKae
wetz7mG/rMIpofJFkoGbU0bBreu0DRztkoo+urP9szO8VlsjG1nBRqVelYBdM6MG
jQIDAQAB
-----END PUBLIC KEY-----"""

        def __init__(self, auth_host: str, audience: str):
            key = jwk.construct(self.rsa_public_key, algorithm='RS256')
            jwk_dict = key.to_dict()
            self.jwks = {"0": jwk_dict}

            super().__init__(auth_host, audience)

        def get_jwks(self):
            return self.jwks

        def get_oauth_config(self):
            return {}

        def sign(self, json):
            return jwt.encode(json, self.rsa_private_key, algorithm="RS256", headers={"kid": "0"})

        def verify(self, token):
            jws.verify(token, self.rsa_public_key, algorithms=["RS256"])

@pytest.fixture(scope='session')
def client():

    if inside_container():
        context_manager = nullcontext()
    else:
        context_manager = DockerCompose(filepath="./", compose_file_name="docker-compose.test.yml")

    with context_manager:

        wait_for(lambda: requests.get(f"{TEST_AUTH_HOST}/.well-known/openid-configuration").json())

        fake_authenticator = NoAuthServerAuthenticator(TEST_AUTH_HOST, TEST_OAUTH2_AUDIENCE)
        micro_templating_app = create_app(project_name=PROJECT_NAME, project_version=PROJECT_VERSION,
                                          db_url=TEST_DB_URL, jinja_env=None, authenticator=fake_authenticator,)
        micro_templating_app.config['TESTING'] = True

        with micro_templating_app.test_client() as client:
            with micro_templating_app.app_context():
                pass
            yield client


@pytest.fixture(scope='session')
def authenticator(client):
    yield client.application.config["AUTH"]
