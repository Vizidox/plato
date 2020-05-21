from .renderer import Renderer, PDF_MIME, OCTET_STREAM, PNG_MIME
from .jinja_formatters import format_year, format_month, num_to_ordinal, of_month_year, format_dates
ALL_AVAILABLE_MIME_TYPES = list(Renderer.renderers.keys())
AVAILABLE_IMG_MIME_TYPES = [key for key in Renderer.renderers.keys() if key.startswith("image")]

FORMATTERS = [format_year, format_month, num_to_ordinal, of_month_year, format_dates]