from datetime import datetime
from typing import Any

DEFAULT_LANGUAGE = "es"

_MESSAGES: dict[str, dict[str, dict[str, str]]] = {
    "es": {
        "event_updated": {
            "title": "Evento actualizado",
            "body": '"{title}" fue modificado por el organizador.',
        },
        "event_cancelled": {
            "title": "Evento cancelado",
            "body": '"{title}" fue cancelado por el organizador.',
        },
        "poll_updated": {
            "title": "Encuesta actualizada",
            "body": '"{title}" fue modificada por el organizador. Revisá tu disponibilidad.',
        },
        "poll_cancelled": {
            "title": "Encuesta cancelada",
            "body": '"{title}" fue cancelada por el organizador.',
        },
        "poll_resolved": {
            "title": "Se confirmó la fecha",
            "body": '"{title}" quedó confirmado para el {date}.',
        },
    },
    "en": {
        "event_updated": {
            "title": "Event updated",
            "body": '"{title}" was changed by the organizer.',
        },
        "event_cancelled": {
            "title": "Event cancelled",
            "body": '"{title}" was cancelled by the organizer.',
        },
        "poll_updated": {
            "title": "Poll updated",
            "body": '"{title}" was changed by the organizer. Check your availability.',
        },
        "poll_cancelled": {
            "title": "Poll cancelled",
            "body": '"{title}" was cancelled by the organizer.',
        },
        "poll_resolved": {
            "title": "Date confirmed",
            "body": '"{title}" is confirmed for {date}.',
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
