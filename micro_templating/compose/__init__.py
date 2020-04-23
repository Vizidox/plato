from .renderer import Renderer, PDF_MIME, OCTET_STREAM, PNG_MIME
ALL_AVAILABLE_MIME_TYPES = Renderer.renderers.keys()
AVAILABLE_IMG_MIME_TYPES = [key for key in Renderer.renderers.keys() if "key".startswith("image")]
