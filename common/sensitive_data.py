from collections.abc import Mapping


SENSITIVE_KEYS = {
    'authorization',
    'api_token',
    'password',
    'password_confirmation',
    'token',
}


def redact_sensitive(value, parent_key=None):
    """Return a report-safe copy without mutating the source object."""
    if parent_key and parent_key.lower() in SENSITIVE_KEYS:
        if parent_key.lower() == 'authorization' and isinstance(value, str):
            scheme = value.split(' ', 1)[0]
            return f'{scheme} ***'
        return '***'

    if isinstance(value, Mapping):
        return {
            key: redact_sensitive(item, str(key))
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact_sensitive(item) for item in value]
    return value
