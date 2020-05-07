"""
Module with the api error messages
"""

# auth
no_auth_header_message = "Expected 'Authorization' header"
unbeary_auth_message = "Authorization header must start with 'Bearer '"
token_is_invalid_message = "Token is invalid: {0}"


#templating
invalid_compose_json = "Invalid compose json: {0}"
template_not_found = "Template '{0}' not found"
unsupported_mime_type = "No supported format in ACCEPT header: {0}, Available formats: {1}"
aspect_ratio_compromised = "Specifying both width and height compromises the template's aspect ratio"
resizing_unsupported = "Resizing unsupported on provided mime_type: {0}"
