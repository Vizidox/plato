from jsonschema.validators import Draft7Validator, extend

QR_CODE_TYPE = "qr_code"


def _qr_type_validator(checker, instance):
    return isinstance(instance, str)


VDXSchemaValidator = extend(
    validator=Draft7Validator,
    type_checker=Draft7Validator.TYPE_CHECKER.redefine(QR_CODE_TYPE, _qr_type_validator)
)
