from typing import NamedTuple, Sequence, TYPE_CHECKING
from . import swag

if TYPE_CHECKING:
    from micro_templating.db.models import Template


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

    @classmethod
    def view_from_template(cls, template: 'Template') -> 'TemplateDetailView':
        """
        Takes a template model and creates a TemplateDetailView.

        Args:
            template: the target template

        Returns:
            TemplateDetailView: A view for the template
        """
        return TemplateDetailView(template_id=template.id,
                                  template_schema=template.schema,
                                  type=template.type,
                                  metadata=template.metadata_)

    @classmethod
    def views_from_templates(cls, templates: Sequence['Template']) -> Sequence['TemplateDetailView']:
        """
        Takes a collection of templates and returns the a collection of views for them.
        Args:
            templates: collection of templates.

        Returns:
            Sequence[TemplateDetailView]: A collection with the views for the supplied templates.
        """
        return [cls.view_from_template(template) for template in templates]
