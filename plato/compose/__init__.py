from .renderer import Renderer, PDF_MIME as PDF_MIME, OCTET_STREAM as OCTET_STREAM, PNG_MIME as PNG_MIME
from .jinja_filters import num_to_ordinal, format_dates, nth

ALL_AVAILABLE_MIME_TYPES = list(Renderer.renderers.keys())
AVAILABLE_IMG_MIME_TYPES = [key for key in Renderer.renderers.keys() if key.startswith("image")]

FILTERS = [num_to_ordinal, format_dates, nth]

__all__ = ['ALL_AVAILABLE_MIME_TYPES', 'AVAILABLE_IMG_MIME_TYPES', 'FILTERS']
