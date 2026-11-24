from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, ValidationError) and isinstance(response.data, dict):
        fields = dict(response.data)
        non_field_errors = fields.pop("non_field_errors", None)
        if non_field_errors:
            error = non_field_errors[0]
        else:
            error = "Помилка валідації"
    elif isinstance(exc, ValidationError):
        fields = {}
        error = response.data[0]
    else:
        fields = {}
        error = response.data.get("detail", "Помилка")

    response.data = {"error": str(error), "fields": fields}
    return response
