from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def get_first_message(value, default):
    if isinstance(value, list):
        if value:
            return get_first_message(value[0], default)
        return default
    if isinstance(value, dict):
        if "detail" in value:
            return get_first_message(value["detail"], default)
        return default
    if value is None:
        return default
    return str(value)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    fields = {}
    if isinstance(exc, ValidationError) and isinstance(response.data, dict):
        fields = dict(response.data)
        non_field_errors = fields.pop("non_field_errors", None)
        error = get_first_message(non_field_errors, "Помилка валідації")
    elif isinstance(exc, ValidationError):
        error = get_first_message(response.data, "Помилка валідації")
    else:
        error = get_first_message(response.data, "Помилка")

    response.data = {"error": error, "fields": fields}
    return response
