from django.core.exceptions import ValidationError


class PasswordComplexityValidator:
    message = "Пароль має містити хоча б одну літеру і одну цифру."

    def validate(self, password, user=None):
        has_letter = any(char.isalpha() for char in password)
        has_digit = any(char.isdigit() for char in password)
        if not has_letter or not has_digit:
            raise ValidationError(self.message, code="password_too_simple")

    def get_help_text(self):
        return self.message
