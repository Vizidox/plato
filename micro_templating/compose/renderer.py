import io
import tempfile
from abc import abstractmethod, ABC
from flask import current_app
from jmespath import search
from mimetypes import guess_extension
from typing import Optional, Type, ClassVar, Dict, List
from qrcode import make
from tempfile import TemporaryDirectory
from weasyprint import HTML

from micro_templating.compose.types import QR_CODE_TYPE
from micro_templating.db.models import Template


class Renderer(ABC):
    """
    Renderer is a factory for every Renderer subclass.

    Typical usage:

        Renderer.build_renderer('application/pdf', /home/my_user/static/, /home/my_user/my_template/static/)

    You may also create your own renderer by extending 'Renderer' and registering it in the factory by using the
    'renderer' decorator like so:

    @Renderer.renderer()
    class MyRenderer(Renderer):
        ...

    """
    renderers: ClassVar[Dict[str, 'Renderer']] = dict()

    def __init__(self, template_model: Template, compose_data: dict,
                 partner_static_directory: str, template_static_directory: str):
        self.template_model = template_model
        self.compose_data = compose_data
        self.partner_static_directory = partner_static_directory
        self.template_static_directory = template_static_directory

    def compose_html(self, compose_data: Optional[dict] = None) -> str:
        jinjaenv = current_app.config["JINJENV"]

        if compose_data is None:
            compose_data = self.compose_data

        template = jinjaenv.get_template(
            name=f"{self.template_model.partner_id}/{self.template_model.id}/{self.template_model.id}"
        )  # template id works for the file as well

        composed_html = template.render(
            p=compose_data,
            partner_static=self.partner_static_directory,
            template_static=self.template_static_directory
        )

        return composed_html

    @abstractmethod
    def render(self) -> io.BytesIO:
        """
        Renders Template onto a a stream according to the Renderer's MIME type.

        """
        ...

    @classmethod
    @abstractmethod
    def mime_type(cls) -> str:
        """
        MIME type for the renderer. Must be implemented by subclass.
        e.g: 'text/plain', 'application/pdf'
        """
        ...

    @classmethod
    def file_extension(cls) -> str:
        """
        File extension for the renderer. Guesses it using mimetypes.py library.
        e.g: 'text/plain', 'application/pdf'
        """
        return guess_extension(cls.mime_type())

    @classmethod
    def build_renderer(cls, mime_type: str, *args) -> Optional[Type['Renderer']]:
        """
        Factory method for 'Renderer' subclasses registered with @Renderer.renderer()

        Args:
            mime_type: the desired renderer output as a MIME type. e.g 'application/PDF'
            *args: the arguments to be passed to the specific constructor, by default same as Renderer.__init__.
        Raises:
            AssertionError: when mime_type is not part of the registered renderers.
        Returns:
            Renderer: renderer for the desired mime_type output.
        """

        assert mime_type in cls.renderers
        sub_renderer = cls.renderers.get(mime_type)

        return sub_renderer(*args)

    @classmethod
    def renderer(cls):
        """
        Decorator to be used when registering a new renderer.

        Returns:
            the renderer type
        """
        def wrapper(type_: Type['Renderer']) -> Type['Renderer']:
            assert issubclass(type_, Renderer)
            cls.renderers[type_.mime_type()] = type_
            return type_
        return wrapper

    def qr_render(self, output_folder: str):
        """
        Render QR codes, altering self.compose_data to replace qr_code properties with the filepath to their renders
        Args:
            output_folder: where to store the QR images renderer

        Alters self.compose with qr types

        """
        qr_schema_paths = list()

        def find_qr_paths(dict_path: List[str], current_dict: dict):
            """
            Collects all the "type: qr_code" key paths on the nested jsonschema and stores them on qr_schema_paths.
            Dict_path is used to iterate what keys lead where, give an empty list().

            Args:
                dict_path: initially empty.
                current_dict: jsonschema dict to be iterated
            """
            dict_path = dict_path[:]
            json_schema_type = current_dict["type"]
            if json_schema_type == "object":
                for field_name, new_dict in current_dict["properties"].items():
                    dict_path.append(field_name)
                    find_qr_paths(dict_path, new_dict)
            elif json_schema_type == QR_CODE_TYPE:
                qr_schema_paths.append(dict_path)
            return

        def set_nested(key_list: List[str], dict_: dict, value: str):
            """
            Sets dict_[key1, key2, ...] = value
            Args:
                key_list: Nested key list
                dict_: Dict to be iterated with key_list
                value: Value to be set
            """
            for key in key_list[:-1]:
                dict_ = dict_[key]
            dict_[key_list[-1]] = value

        find_qr_paths(list(), self.template_model.schema)

        for i, qr_schema_path in enumerate(qr_schema_paths):
            with open(f"{output_folder}/{i}.png", mode="wb") as qr_file:
                qr_value = search(".".join(qr_schema_path), self.compose_data)
                img = make(qr_value)
                img.save(qr_file)
                set_nested(qr_schema_path, self.compose_data, qr_file.name)

        return self.compose_data


@Renderer.renderer()
class PdfRenderer(Renderer):
    """
    PDF Renderer which uses weasyprint to generate PDF documents.
    """

    def render(self) -> io.BytesIO:
        with TemporaryDirectory() as temp_render_directory:
            self.qr_render(temp_render_directory)
            html_string = self.compose_html()
            with tempfile.NamedTemporaryFile() as target_file_html:
                html = HTML(string=html_string)
                html.write_pdf(target_file_html.name)
                with open(target_file_html.name, mode='rb') as temp_file_stream:
                    return io.BytesIO(temp_file_stream.read())

    @classmethod
    def mime_type(cls):
        return 'application/pdf'
