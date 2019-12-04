from flask import Flask
from flask_cors import CORS
from flasgger import Swagger

app = Flask(__name__)

cors = CORS(app)
swag = Swagger(app)
