from typing import NamedTuple, List

from flasgger.base import SwaggerDefinition


class SwaggerViewCatalogue:
    """
    Swagger View Catalogue

    A catalogue of all the Views relevant for the Swagger specification.
    To be used with `flasgger.base.Swagger' by appending the `swagger_definitions' property to Swagger.definition_models

        swag = Swagger(app, template=swagger_template, config=swagger_config)
        swag.definition_models.append(*SwaggerViewCatalogue.swagger_definitions)

    Attributes:
        swagger_definitions: A List of flasgger.base.SwaggerDefinition with all the definitions
         created through swagger_info
    """
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
