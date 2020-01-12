from typing import NamedTuple, List

from flasgger.base import SwaggerDefinition


class SwaggerViewCatalogue:
    swagger_definitions: List[SwaggerDefinition] = list()

    @classmethod
    def swagger_info(cls, name, tags=None):
        """
        Decorator to add class based definitions
        """

        def wrapper(obj):
            cls.swagger_definitions.append(SwaggerDefinition(name, obj, tags=tags))
            return obj

        return wrapper


@SwaggerViewCatalogue.swagger_info("TemplateDetail")
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
