# Create Template

A Plato template contains two parts:

* An HTML file (plus any added static files), which will be used to produce the final, composed file.
* A json schema structure, defining all fields required by the template to be composed.

To create a template, first you need to create your base HTML file. There is nothing special about this file, but there are
some details that you should bear in mind:

* It is ideal for the template to be a single HTML file, although importing is possible.
* The static content can be imported as well, but composing the template into HTML will not work. For that scenario, it
  is ideal to embed all static content directly on the single HTML file.

When you are done with your template HTML file, you need to identify the fields that are to be placeholders for the template. 
Plato uses [Jinja](https://jinja.palletsprojects.com) to compose the variable values on to the placeholders. For example,
if you have want to fill a specific place on the template with a user's name, then you write {{ p.username }}, where *username*
is a field on the JSON schema. For more details on how you can customize your template with Jinja, check 
the [template designer page](https://jinja.palletsprojects.com/en/3.1.x/templates/).

<aside class="notice">
  If you are importing any images or static content from the static folder, the source on the HTML field should be: 
  `src="file://{{ template_static }}<IMAGE_NAME>"`, with IMAGE_NAME changed to the actual file name. *template_static* includes the path to the static content folder.
</aside>

There are also some filters available that allow you to customize the appearance of the values added to the placeholders. For example, if you pass in a string and you want
it converted to lower-case, then write the following: {{ p.name | lower }}. Multiple filters can be chained, and they are executed from the right to the left.
All [Jinja pre-defined filters}{https://jinja.palletsprojects.com/templates/#filters} can be used, as well as some custom filters that have been added:

* *format_dates*, to format any date. Use with no argument to format to the default option (1 January 2020), or pass in 
  any valid [babel](https://babel.pocoo.org/en/latest/dates.html#date-fields) format for other options. 
* *num_to_ordinal*, change a cardinal number (in string or int) to ordinal format. For example, '1' to '1st' or '16' to '16th'.
* *nth*, returns the suffix of an ordinal number. For example, '1' returns 'st' and '16' returns 'th'.

After you are done with the HTML file, then create the corresponding JSON Schema, and add everything to Plato, according to instructions on the [Quick Start](#add-templates-to-plato) guide.

<aside class="warning">
  [WeasyPrint](https://weasyprint.org/) is used to convert the HTML template to PDF, so make sure you do not use any unsupported HTML tag.
</aside>