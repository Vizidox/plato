import json
import uuid
import zipfile
from http import HTTPStatus
from mimetypes import guess_extension
from typing import Callable, Tuple

from accept_types import get_best_match
from flask import jsonify, request, Flask, send_file
from jsonschema import ValidationError
from sqlalchemy import String, cast as db_cast
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from plato.compose import PDF_MIME, ALL_AVAILABLE_MIME_TYPES
from plato.compose.renderer import compose, RendererNotFound, PNG_MIME, InvalidPageNumber
from plato.views.views import TemplateDetailView
from .db import db
from .db.models import Template
from .error_messages import invalid_compose_json, template_not_found, unsupported_mime_type, aspect_ratio_compromised, \
    resizing_unsupported, single_page_unsupported, negative_number_invalid, template_already_exists, invalid_zip_file, \
    invalid_directory_structure, invalid_json_field
from plato.util.s3_bucket_util import upload_template_files_to_s3, get_file_s3, NoIndexTemplateFound
from .settings import S3_TEMPLATE_DIR, S3_BUCKET, TEMPLATE_DIRECTORY
from plato.util.setup_util import write_files
from .util.path_util import template_path, tmp_zipfile_path, static_path


class UnsupportedMIMEType(Exception):
    """
    Exception to be raised when the mime type requested is not supported
    """
    ...


def initialize_api(app: Flask):
    """
    Initializes Flask app with the microservice endpoints.

    Args:
        app: The Flask app
    Returns:
    """

    @app.route("/templates/<string:template_id>", methods=['GET'])
    def template_by_id(template_id: str):
        """
        Returns template information
        ---
        parameters:
          - name: template_id
            in: path
            type: string
            required: true
        responses:
          200:
            description: Information on the template
            schema:
              $ref: '#/definitions/TemplateDetail'
          404:
            description: Template not found
        tags:
           - template
        """
        try:

            template: Template = Template.query.filter_by(id=template_id).one()
            view = TemplateDetailView.view_from_template(template)
            return jsonify(view._asdict())

        except NoResultFound:
            return jsonify({"message": template_not_found.format(template_id)}), HTTPStatus.NOT_FOUND

    @app.route("/templates/", methods=['GET'])
    def templates():
        """
        Returns template information
        ---
        parameters:
          - in: query
            name: tags
            type: array
            collectionFormat: multi
            items:
                type: string
        responses:
          200:
            description: Information on all templates available
            type: array
            items:
                $ref: '#/definitions/TemplateDetail'
        tags:
           - template
        """

        tags = request.args.getlist("tags", type=str)
        template_query = Template.query
        if tags:
            template_query = template_query.filter(Template.tags.contains(db_cast(tags, ARRAY(String))))

        json_views = [TemplateDetailView.view_from_template(template)._asdict() for
                      template in
                      template_query]

        return jsonify(json_views)

    @app.route("/template/create", methods=['POST'])
    def create_template():
        """
        Creates a template
        ---
        consumes:
        - multipart/form-data
        parameters:
            - in: formData
              name: zipfile
              type: file
              required: true
              description: Contents of ZIP file
            - in: formData
              required: true
              name: template_details
              type: string
              format: application/json
              properties:
                  title:
                    type: string
                    description: The template id
                    example: template_id
                  schema:
                    type: object
                    properties: {}
                  type:
                    # default Content-Type for string is `application/octet-stream`
                    type: string
                  metadata:
                    type: object
                    properties: {}
                  example_composition:
                    type: object
                    properties: {}
                  tags:
                     type: array
                     items:
                       type: string
              required: true
              description: Contents of template
        responses:
          201:
            description: Information of newly created template
            type: array
            items:
                $ref: '#/definitions/TemplateDetail'
          400:
            description: The file does not have the correct directory structure
          409:
            description: The template already exists
          415:
            description: The file is not a ZIP file
        tags:
           - template
        """

        is_zipfile, zip_file_name = _save_and_validate_zipfile()
        if not is_zipfile:
            return jsonify({"message": invalid_zip_file}), HTTPStatus.UNSUPPORTED_MEDIA_TYPE

        template_details = request.form.get('template_details')
        template_entry_json = json.loads(template_details)

        template_id = template_entry_json['title']
        new_template = Template.from_json_dict(template_entry_json)

        try:
            # uploads template files from zip file to S3
            upload_template_files_to_s3(template_id, S3_TEMPLATE_DIR, zip_file_name, S3_BUCKET)
            _load_and_write_template_from_s3(template_id)

            # saves template json into database
            db.session.add(new_template)
            db.session.commit()
        except IntegrityError:
            return jsonify({"message": template_already_exists.format(template_id)}), HTTPStatus.CONFLICT
        except FileNotFoundError:
            return jsonify({"message": invalid_directory_structure}), HTTPStatus.BAD_REQUEST

        return jsonify(TemplateDetailView.view_from_template(new_template)._asdict()), HTTPStatus.CREATED

    @app.route("/template/<string:template_id>/update", methods=['PUT'])
    def update_template(template_id: str):
        """
        Update a template
        ---
        consumes:
        - multipart/form-data
        parameters:
            - name: template_id
              in: path
              type: string
              required: true
            - in: formData
              name: zipfile
              type: file
              required: true
              description: Contents of ZIP file
            - in: formData
              required: true
              name: template_details
              type: string
              format: application/json
              properties:
                  schema:
                    type: object
                    properties: {}
                  type:
                    # default Content-Type for string is `application/octet-stream`
                    type: string
                  metadata:
                    type: object
                    properties: {}
                  example_composition:
                    type: object
                    properties: {}
                  tags:
                     type: array
                     items:
                       type: string
              required: true
              description: Contents of template
        responses:
          200:
            description: Information of updated template
            type: array
            items:
                $ref: '#/definitions/TemplateDetail'
          400:
            description: The file does not have the correct directory structure
          404:
            description: Template not found in database
          415:
            description: The file is not a ZIP file
        tags:
           - template
        """
        is_zipfile, zip_file_name = _save_and_validate_zipfile()
        if not is_zipfile:
            return jsonify({"message": invalid_zip_file}), HTTPStatus.UNSUPPORTED_MEDIA_TYPE

        template_details = request.form.get('template_details')
        template_entry_json = json.loads(template_details)

        try:
            # update template into database
            template = Template.query.filter_by(id=template_id).first_or_404()
            template.update_from_json_dict(template_entry_json)
            db.session.commit()

            # uploads template files from zip file to S3
            upload_template_files_to_s3(template_id, S3_TEMPLATE_DIR, zip_file_name, S3_BUCKET)
            _load_and_write_template_from_s3(template_id)
        except NoResultFound:
            return jsonify({"message": template_not_found.format(template_id)}), HTTPStatus.NOT_FOUND
        except FileNotFoundError:
            return jsonify({"message": invalid_directory_structure}), HTTPStatus.BAD_REQUEST
        except KeyError as e:
            return jsonify({"message": invalid_json_field.format(e.args)}), HTTPStatus.BAD_REQUEST

        return jsonify(TemplateDetailView.view_from_template(template)._asdict())

    @app.route("/template/<string:template_id>/update_json", methods=['PATCH'])
    def update_json_template(template_id: str):
        """
        Update a template model
        ---
        consumes:
        - application/json
        parameters:
            - name: template_id
              in: path
              type: string
              required: true
            - in: body
              required: true
              name: template_details
              schema:
                type: object
                properties:
                    schema:
                      type: object
                      properties: {}
                    type:
                      # default Content-Type for string is `application/octet-stream`
                      type: string
                    metadata:
                      type: object
                      properties: {}
                    example_composition:
                      type: object
                      properties: {}
                    tags:
                       type: array
                       items:
                         type: string
              required: true
              description: Contents of a template model
        responses:
          200:
            description: Information of updated template
            type: array
            items:
                $ref: '#/definitions/TemplateDetail'
          400:
            description: The input is not in the correct form
          404:
            description: Template not found in database
        tags:
           - template
        """

        template_details = request.get_json()
        try:
            # update template into database
            template = Template.query.filter_by(id=template_id).first_or_404()
            template.update_fields(**template_details)
            db.session.commit()
        except NoResultFound:
            return jsonify({"message": template_not_found.format(template_id)}), HTTPStatus.NOT_FOUND
        except KeyError as e:
            return jsonify({"message": invalid_json_field.format(e.args)}), HTTPStatus.BAD_REQUEST

        return jsonify(TemplateDetailView.view_from_template(template)._asdict())

    def _load_and_write_template_from_s3(template_id: str) -> None:
        """
        Fetches template data from S3 Bucket and saves it locally

        Args:
            template_id (str): The template id
        """

        template_paths = [template_path(S3_TEMPLATE_DIR, template_id), static_path(S3_TEMPLATE_DIR, template_id)]
        for path in template_paths:

            template_files = get_file_s3(bucket_name=S3_BUCKET, url=path,
                                         s3_template_directory=S3_TEMPLATE_DIR)
            if not template_files:
                raise NoIndexTemplateFound(template_id)
            write_files(files=template_files, target_directory=TEMPLATE_DIRECTORY)

    def _save_and_validate_zipfile() -> Tuple[bool, str]:
        """
        Saves in tmp directory and checks if file is a ZIP file.

        Returns:
            bool: Indicates if the file is a ZIP file
            str: ZIP filename it was saved as in the tmp directory

        """
        zip_uid = str(uuid.uuid4())
        zip_file_name = f"zipfile_{zip_uid}"
        zip_file = request.files.get('zipfile')

        zip_file.save(tmp_zipfile_path(zip_file_name))
        is_zipfile = zipfile.is_zipfile(zip_file)

        return is_zipfile, zip_file_name

    @app.route("/template/<string:template_id>/compose", methods=["POST"])
    def compose_file(template_id: str):
        """
        Composes file based on the template
        ---
        consumes:
            - application/json
        produces:
            - application/pdf
            - image/png
            - text/html
        parameters:
            - name: template_id
              in: path
              type: string
              required: true
            - in: body
              name: schema
              description: body to compose file with, must be according to the template schema
              schema:
                type: object
            - in: header
              name: accept
              required: false
              type: string
              enum: [application/pdf, image/png, text/html]
              description: MIME type(s) to determine what kind of file is outputted
            - in: query
              name: page
              required: false
              type: integer
              description: Intended page to print
            - in: query
              name: height
              required: false
              type: integer
              description: Intended height for image output
            - in: query
              name: width
              required: false
              type: integer
              description: Intended width for image output
        responses:
          200:
            description: composed file
            schema:
              type: file
          400:
            description: Invalid compose data for template schema
          404:
             description: Template not found
          406:
             description: Unsupported MIME type for file
        tags:
           - compose
           - template
        """
        return _compose(template_id, "compose", lambda t: request.get_json())

    @app.route("/template/<string:template_id>/example", methods=["GET"])
    def example_compose(template_id: str):
        """
        Gets example file based on the template
        ---
        consumes:
            - application/json
        produces:
            - application/pdf
            - image/png
            - text/html
        parameters:
            - name: template_id
              in: path
              type: string
              required: true
            - in: header
              name: accept
              required: false
              type: string
              enum: [application/pdf, image/png, text/html]
            - in: query
              name: page
              required: false
              type: integer
              description: Intended page to print
            - in: query
              name: height
              required: false
              type: integer
              description: Intended height for image output
            - in: query
              name: width
              required: false
              type: integer
              description: Intended width for image output
        responses:
          200:
            description: composed file
            schema:
              type: file
          404:
             description: Template not found
          406:
             description: Unsupported MIME type for file
        tags:
           - compose
           - template
        """
        return _compose(template_id, "example", lambda t: t.example_composition)

    def _compose(template_id: str,
                 file_name: str,
                 compose_retrieval_function: Callable[[Template], dict]):
        width = request.args.get("width", type=int)
        height = request.args.get("height", type=int)
        page = request.args.get("page", type=int)

        accept_header = request.headers.get("Accept", PDF_MIME)
        mime_type = get_best_match(accept_header, ALL_AVAILABLE_MIME_TYPES)

        try:
            if mime_type is None:
                raise UnsupportedMIMEType(accept_header)

            if (width is not None or height is not None) and mime_type != PNG_MIME:
                return jsonify({"message": resizing_unsupported.format(mime_type)}), HTTPStatus.BAD_REQUEST

            if page is not None and mime_type != PNG_MIME:
                return jsonify({"message": single_page_unsupported.format(mime_type)}), HTTPStatus.BAD_REQUEST

            if width is not None and height is not None:
                return jsonify({"message": aspect_ratio_compromised}), HTTPStatus.BAD_REQUEST

            if page is not None and page < 0:
                return jsonify({"message": negative_number_invalid.format(page)}), HTTPStatus.BAD_REQUEST

            compose_params = {}
            if width is not None:
                compose_params["width"] = width
            if height is not None:
                compose_params["height"] = height
            if page is not None:
                compose_params["page"] = page

            template_model: Template = Template.query.filter_by(id=template_id).one()
            compose_data = compose_retrieval_function(template_model)
            composed_file = compose(template_model, compose_data, mime_type, **compose_params)
            return send_file(composed_file, mimetype=mime_type, as_attachment=True,
                             attachment_filename=f"{file_name}{guess_extension(mime_type)}"), HTTPStatus.OK
        except (RendererNotFound, UnsupportedMIMEType):
            return jsonify(
                {"message": unsupported_mime_type.format(accept_header, ", ".join(ALL_AVAILABLE_MIME_TYPES))}), HTTPStatus.NOT_ACCEPTABLE
        except InvalidPageNumber as e:
            return jsonify({"message": e.message}), HTTPStatus.BAD_REQUEST
        except NoResultFound:
            return jsonify({"message": template_not_found.format(template_id)}), HTTPStatus.NOT_FOUND
        except ValidationError as ve:
            return jsonify({"message": invalid_compose_json.format(ve.message)}), HTTPStatus.BAD_REQUEST
