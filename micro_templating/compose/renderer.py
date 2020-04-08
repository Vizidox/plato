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
from jsonschema import validate as validate_schema

from micro_templating.db.models import Template
from micro_templating.settings import TEMPLATE_DIRECTORY


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

    def __init__(self, template_model: Template,
                 partner_static_directory: str, template_static_directory: str):
        self.template_model = template_model
        self.partner_static_directory = partner_static_directory
        self.template_static_directory = template_static_directory

    def compose_html(self, compose_data: dict) -> str:
        jinjaenv = current_app.config["JINJENV"]

        template = jinjaenv.get_template(
            name=f"{self.template_model.partner_id}/{self.template_model.id}/{self.template_model.id}"
        )  # template id works for the file as well

        composed_html = template.render(
            p=compose_data,
            partner_static=self.partner_static_directory,
            template_static=self.template_static_directory
        )

        return composed_html

    def render(self, compose_data: dict) -> io.BytesIO:
        """
        Renders Template onto a a stream according to the Renderer's MIME type.

        """
        with TemporaryDirectory() as temp_render_directory:
            compose_data = self.qr_render(temp_render_directory, compose_data)
            html_string = self.compose_html(compose_data)
            return self.print(html_string)

    @abstractmethod
    def print(self, html: str) -> io.BytesIO:
        """
        Print the file according to the Renderer MIME type.

        Args:
            html: The HTML to be printed

        Returns:
            io.BytesIO: A file stream with the Rendere's MIME type.
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
    def build_renderer(cls, mime_type: str, *args, **kwargs) -> Optional[Type['Renderer']]:
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

        return sub_renderer(*args, **kwargs)

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

    def qr_render(self, output_folder: str, compose_data: dict):
        """
        Render QR codes, altering self.compose_data to replace qr_code properties with the filepath to their renders
        Args:
            output_folder: where to store the QR images renderer
            compose_data: the data to fill the templatye with
        Returns:
            dict: altered compose_data
        """
        qr_schema_paths = self.template_model.get_qr_entries()

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

        for i, qr_schema_path in enumerate(qr_schema_paths):
            with open(f"{output_folder}/{i}.png", mode="wb") as qr_file:
                qr_value = search(qr_schema_path, compose_data)
                img = make(qr_value)
                img.save(qr_file)
                set_nested(qr_schema_path.split("."), compose_data, qr_file.name)

        return compose_data


@Renderer.renderer()
class PdfRenderer(Renderer):
    """
    PDF Renderer which uses weasyprint to generate PDF documents.
    """

    def print(self, html_string: str) -> io.BytesIO:

        with tempfile.NamedTemporaryFile() as target_file_html:
            html = HTML(string=html_string)
            html.write_pdf(target_file_html.name)
            with open(target_file_html.name, mode='rb') as temp_file_stream:
                return io.BytesIO(temp_file_stream.read())

    @classmethod
    def mime_type(cls):
        return 'application/pdf'


def compose(template: Template, compose_data: dict, mime_type: str) -> io.BytesIO:
    """
    Composes a file of the given mime_type using the compose_data to fill the given template.

    Args:
        template: The Template model to be used in the composition
        mime_type: The desired output MIME type.
        compose_data: The dict with the data to fill the template.

    Raises:
        jsonschema.exceptions.ValidationError: When the compose_data is not valid for a given template
    Returns:
        io.BytesIO: The Byte stream for the composed file.
    """
    validate_schema(instance=compose_data, schema=template.schema)

    partner_static_folder = f"{TEMPLATE_DIRECTORY}/static/{template.partner_id}/"
    template_static_folder = f"{TEMPLATE_DIRECTORY}/static/{template.partner_id}/{template.id}/"

    renderer = Renderer.build_renderer(mime_type,
                                       template_model=template,
                                       partner_static_directory=partner_static_folder,
                                       template_static_directory=template_static_folder
                                       )

    return renderer.render(compose_data)
