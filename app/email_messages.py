from datetime import datetime
from typing import Any

DEFAULT_LANGUAGE = "es"

_MESSAGES: dict[str, dict[str, dict[str, str]]] = {
    "es": {
        "email_verification": {
            "subject": "Confirmá tu email en Prendete",
            "html": (
                "<p>Hola {first_name},</p>"
                "<p>Confirmá tu email para activar tu cuenta en Prendete:</p>"
                '<p><a href="{link}">Confirmar mi email</a></p>'
                "<p>Este link vence en 7 días.</p>"
            ),
        },
        "password_reset": {
            "subject": "Recuperar contraseña en Prendete",
            "html": (
                "<p>Hola {first_name},</p>"
                "<p>Pediste restablecer tu contraseña. Hacé click para elegir una nueva:</p>"
                '<p><a href="{link}">Restablecer contraseña</a></p>'
                "<p>Este link vence en 1 hora. Si no fuiste vos, ignorá este mail.</p>"
            ),
        },
    },
    "en": {
        "email_verification": {
            "subject": "Confirm your email on Prendete",
            "html": (
                "<p>Hi {first_name},</p>"
                "<p>Confirm your email to activate your Prendete account:</p>"
                '<p><a href="{link}">Confirm my email</a></p>'
                "<p>This link expires in 7 days.</p>"
            ),
        },
        "password_reset": {
            "subject": "Reset your password on Prendete",
            "html": (
                "<p>Hi {first_name},</p>"
                "<p>You asked to reset your password. Click to choose a new one:</p>"
                '<p><a href="{link}">Reset password</a></p>'
                "<p>This link expires in 1 hour. If this wasn't you, ignore this email.</p>"
            ),
        },
    },
}


def _format_datetime(value: datetime, language: str) -> str:
    if language == "en":
        return value.strftime("%m/%d/%Y at %I:%M %p").replace(" 0", " ")
    return value.strftime("%d/%m/%Y a las %H:%M")


def build_message(key: str, language: str | None, **params: Any) -> dict[str, str]:
    lang = language if language in _MESSAGES else DEFAULT_LANGUAGE
    formatted_params = {
        name: _format_datetime(value, lang) if isinstance(value, datetime) else value
        for name, value in params.items()
    }
    template = _MESSAGES[lang][key]
    return {field: text.format(**formatted_params) for field, text in template.items()}
