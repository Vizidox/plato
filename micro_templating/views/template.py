from typing import NamedTuple

from ..flask_app import swag


@swag.definition("TemplateDetail")
class TemplateDetailView(NamedTuple):
    """
    Template Detail
    ---
    properties:
        template_id:
            type: string
            description: template id
        template_schema:
            type: object
            description: jsonschema for template
        type:
            type: string
            description: template MIME type
        metadata:
            type: object
            description: a collection on property values defined by the resource owner at the template conception
    """
    template_id: str
    template_schema: dict
    type: str
    metadata: dict
