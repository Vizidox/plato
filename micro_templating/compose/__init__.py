from .renderer import Renderer, PDF_MIME, OCTET_STREAM, PNG_MIME
from .jinja_formatters import num_to_ordinal, format_dates, nth
ALL_AVAILABLE_MIME_TYPES = list(Renderer.renderers.keys())
AVAILABLE_IMG_MIME_TYPES = [key for key in Renderer.renderers.keys() if key.startswith("image")]

FORMATTERS = [num_to_ordinal, format_dates, nth]