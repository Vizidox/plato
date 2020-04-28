# -*- coding: utf-8 -*-
import boto3
import tempfile
import pytest
import pathlib
from moto import mock_s3
from smart_open import s3
from micro_templating.setup_util import load_templates, NoStaticContentFound, NoIndexTemplateFound
from tempfile import TemporaryDirectory
from micro_templating.db.models import Template, db
from typing import List


class TemplateMeta:
    """
    Each instance for this class contains necessary data for each template for easier testing
    """
    def __init__(self, partner_id: str, template_id: str, static_files: List[str], template_files: List[str], template: Template):
        self.partner_id = partner_id
        self.template_id = template_id
        self.static_files = static_files
        self.template_files = template_files
        self.template = template

    def save(self) -> None:
        """
        Save the template into DB
        """
        if self.template is None:
            raise Exception("template is None")
        db.session.add(self.template)

def create_template(template_dir: str, partner_id: str, template_id: str) -> TemplateMeta:
    """
    Create necessary stuff for testing that is bundled into 1 TemplateMeta instance
    """
    template = Template(partner_id=partner_id, id_=template_id, schema={},
                        type_="text/html", tags=['test_tags'], metadata={})
    static_files = [f"{template_dir}/static/{partner_id}/{template_id}/abc.png"]
    template_files = [f"{template_dir}/templates/{partner_id}/{template_id}/{template_id}"]
    template_meta = TemplateMeta(partner_id=partner_id, template_id=template_id, static_files=static_files, template_files=template_files, template=template)
    return template_meta

def delete_template(template: Template):
    """
    delete a template
    """
    db.session.delete(template)

@mock_s3
def test_template_loading(client):
    """
    Test the retrieval of necessary directory and file in a s3 bucket
    """
    conn = boto3.resource('s3', region_name='eu-central-1')
    bucket_name = "test_template_bucket"
    conn.create_bucket(Bucket=bucket_name)
    encoding = "utf-8"

    app = client.application
    app.test_request_context().push()

    ############################### S3 data preparation #######################
    # Prepare 2 templates on S3
    partner_template = [("partner_id1", "template_id1"), ("partner_id2", "template_id2")]
    for partner_id, template_id in partner_template:
        static_file = f"static/{partner_id}/{template_id}/abc.png"
        template_file = f"templates/{partner_id}/{template_id}/{template_id}"
        urls = [static_file, template_file]
        for url in urls:
            with s3.open(bucket_name, key_id=url, mode="wb") as file:
                file.write(f"I am file {url}!".encode(encoding))

    # static loss case
    template_file = f"templates/lost_static_partner_id/lost_static_template_id/lost_static_template_id"
    with s3.open(bucket_name, key_id=template_file, mode="wb") as file:
        file.write(f"I am file {url}!".encode(encoding))

    # template loss case
    static_file = f"static/lost_template_partner_id/lost_template_template_id/abc.png"
    with s3.open(bucket_name, key_id=static_file, mode="wb") as file:
        file.write(f"I am file {url}!".encode(encoding))

    ######################## start testing ########################
    with TemporaryDirectory() as temp:
        template_dir_name = temp + "/abc"
        pathlib.Path(template_dir_name).mkdir(parents=True, exist_ok=True)
        # a random file exist
        random_file = tempfile.NamedTemporaryFile(dir=template_dir_name, delete=False)

        template_1 = create_template(template_dir=template_dir_name, partner_id="partner_id1", template_id="template_id1")
        template_2 = create_template(template_dir=template_dir_name, partner_id="partner_id2", template_id="template_id2")
        template_1.save()
        load_templates(bucket_name, template_dir_name)

        # check if files for template_1 exist
        for file_url_ in template_1.static_files + template_1.template_files:
            file_ = pathlib.Path(file_url_)
            assert file_.exists() == True

        # check if old file in the directory is removed
        assert pathlib.Path(random_file.name).exists() == False

        # check if file for template_2 dont exist, because template_2 is not saved in DB
        for file_url_ in template_2.static_files + template_2.template_files:
            file_ = pathlib.Path(file_url_)
            assert file_.exists() == False

        # check if there is just 1 folder for template_1
        list_static_folders = list(pathlib.Path(f"{template_dir_name}/static").iterdir())
        list_template_folders = list(pathlib.Path(f"{template_dir_name}/templates").iterdir())
        assert len(list_static_folders) == 1
        assert len(list_template_folders) == 1

            ######################## add new template ##############################
        template_2.save()
        load_templates(bucket_name, template_dir_name)

        # Make sure all 2 templates are all available
        for file_url_ in template_1.static_files + template_1.template_files + template_2.static_files + template_2.template_files:
            file_ = pathlib.Path(file_url_)
            assert file_.exists() == True

        # Make sure there are 2 separate folders for 2 templates
        list_static_folders = list(pathlib.Path(f"{template_dir_name}/static").iterdir())
        list_template_folders = list(pathlib.Path(f"{template_dir_name}/templates").iterdir())
        assert len(list_static_folders) == 2
        assert len(list_template_folders) == 2

            ########################## Exception cases ###############################
        # no static content found case
        with pytest.raises(NoStaticContentFound):
            lost_static_template = create_template(template_dir=template_dir_name, partner_id="lost_static_partner_id",
                                         template_id="lost_static_template_id")
            lost_static_template.save()
            load_templates(bucket_name, template_dir_name)

        # delete the static content case
        delete_template(lost_static_template.template)

        # no template content found case
        with pytest.raises(NoIndexTemplateFound):
            list_template_template = create_template(template_dir=template_dir_name, partner_id="lost_template_partner_id",
                                         template_id="lost_template_template_id")
            list_template_template.save()
            load_templates(bucket_name, template_dir_name)
