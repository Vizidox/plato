# Templating Microservice

A python REST API for document composition through jsonschema. 

## Getting Started

These instructions will get the project up and running on your local environment so you can start contributing to the project.
### Prerequisites

* [Python 3.7+](https://www.python.org/)
* [Poetry 1.0+](https://python-poetry.org/)
* [Docker](https://docker.com)
* [Docker-compose](https://docs.docker.com/compose/)

The project depends on [weasyprint](https://weasyprint.org/) for writing PDF from HTML so make sure you have everything
 weasy print needs to run by following the instructions on this [page](https://weasyprint.readthedocs.io/en/latest/install.html#linux). 
 
 The instructions are also available below.
 
 ####Debian/Ubuntu


```bash
sudo apt-get install build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

### Installing

The first thing you should set up is your local .env file.

Do so by copying the template .env by following the step below.

```bash
cp .env.local .env
```

Make sure you fill in the Template directory with an absolute path.
You may use a subdirectory inside of your DATA_DIR.

e.g TEMPLATE_DIRECTORY=/home/carloscoda/projects/templating/data/templates

If using a different S3 bucket than "micro-templating" then change S3_BUCKET to whichever bucket you want to use.

Make sure the bucket is accessible by providing credentials to the service by
 storing the S3 AWS credentials in your DATA_DIR/aws/.  
#### Authentication Server and Database
The templating service uses Postgresql and Keycloak for authentication.
To set up local servers for both you may use the docker-compose file supplied.
 
```bash
cp docker/docker-compose.local.override.yml .
```

Then spin up both containers by running:

```bash
docker-compose up -d auth database
```

You can make sure the auth server is running by accessing http://localhost:8787/auth.
To do the same for the database you may try accessing it through 
```
postgresql://templating:template-pass@localhost:5455/templating
```

Then you have to initialize the DB, which is done through [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/).
Make sure you export the FLASK_APP environment variable as the main.py module beforehand.
```bash
export FLASK_APP=main.py
flask db upgrade
```

You can then run the application by running:
```bash
poetry run python main.py
```

This will make the application available at http://localhost:5000/apidocs/ 
where you can use swagger-ui to interact with the application. Make sure you authenticate with your example client. 
By clicking one of the locks on the page and _Authorize_.


## Running the tests

```bash
poetry run pytest
```

## Deployment

To be added.

## Built With

* [Flask](https://palletsprojects.com/p/flask/) - Web framework
* [Flasgger](https://github.com/flasgger/flasgger) - Swagger 2 specification
* [Poetry](https://maven.apache.org/) - Dependency Management
* [Jinja2](https://palletsprojects.com/p/jinja/) - For HTML composition
* [Weasyprint](https://weasyprint.org/) - For PDF generation from HTML

## Versioning

We use [SemVer](http://semver.org/) for versioning.

## Authors

* **Tiago Santos** - *Initial work* - tiago.santos@vizidox.com

## License

All of the code developed in this project belongs to Vizidox Solutions Limited and any 
distribution or use must be authorized and agreed upon previously according to the
 Vizidox Solutions Limited terms and conditions.

