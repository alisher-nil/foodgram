from rest_framework.exceptions import ValidationError


class NotEmptyValueValidator:
    """Validator for checking that the fields are not empty.

    Raises a ValidationError in following cases:
    - if a field is not provided.
    - if a field is None.
    - if a field is an empty string.
    - if a field is an empty list.
    """

    message = "No {field} provided"

    def __init__(self, fields, message=None):
        self.message = message or self.message
        self.fields = fields

    def __call__(self, attrs):
        errors = {}
        for field in self.fields:
            if not attrs.get(field):
                errors[field] = self.message.format(field=field)
        if errors:
            raise ValidationError(errors)
