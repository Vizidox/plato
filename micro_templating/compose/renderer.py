import io
import tempfile
from abc import abstractmethod, ABC
from mimetypes import guess_extension
from typing import AnyStr, Optional, Type, ClassVar, Dict

from weasyprint import HTML


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

    def __init__(self, partner_static_directory: str, template_static_directory: str):
        self.partner_static_directory = partner_static_directory
        self.template_static_directory = template_static_directory

    @abstractmethod
    def render(self, html: AnyStr) -> io.BytesIO:
        """
        Renders HTML onto a a stream according to the Renderer's MIME type.

        Args:
            html: String that represents the HTML
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


@Renderer.renderer()
class PdfRenderer(Renderer):
    """
    PDF Renderer which uses weasyprint to generate PDF documents.
    """

    def render(self, html: AnyStr) -> io.BytesIO:
        with tempfile.NamedTemporaryFile() as target_file_html:
            html = HTML(string=html)
            html.write_pdf(target_file_html.name)
            with open(target_file_html.name, mode='rb') as temp_file_stream:
                return io.BytesIO(temp_file_stream.read())

    @classmethod
    def mime_type(cls):
        return 'application/pdf'
