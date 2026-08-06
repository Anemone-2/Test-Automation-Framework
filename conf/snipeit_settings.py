import os
from dataclasses import dataclass, field
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = PROJECT_ROOT / 'infra' / 'snipeit' / '.env'


def _read_env_file(path):
    values = {}
    if not path.exists():
        raise RuntimeError(
            f'Snipe-IT environment file not found: {path}. '
            'Copy infra/snipeit/.env.example to .env and configure it first.'
        )

    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


@dataclass(frozen=True)
class SnipeItSettings:
    base_url: str
    api_token: str = field(repr=False)
    admin_username: str
    admin_password: str = field(repr=False)
    admin_email: str
    api_timeout: float
    browser: str
    driver_path: str
    headless: bool
    ui_timeout: float
    db_host: str
    db_port: int
    db_name: str
    db_username: str
    db_password: str = field(repr=False)

    @classmethod
    def load(cls):
        env_path = Path(os.getenv('SNIPEIT_ENV_FILE', DEFAULT_ENV_FILE))
        file_values = _read_env_file(env_path)

        def value(name, default=None):
            return os.getenv(name, file_values.get(name, default))

        base_url = value('SNIPEIT_BASE_URL', value('APP_URL'))
        api_token = value('SNIPEIT_API_TOKEN')
        missing = [
            name for name, configured in (
                ('SNIPEIT_BASE_URL', base_url),
                ('SNIPEIT_API_TOKEN', api_token),
            ) if not configured
        ]
        if missing:
            raise RuntimeError(
                'Missing required Snipe-IT settings: ' + ', '.join(missing)
            )

        return cls(
            base_url=base_url.rstrip('/'),
            api_token=api_token,
            admin_username=value('SNIPEIT_ADMIN_USERNAME', 'admin'),
            admin_password=value('SNIPEIT_ADMIN_PASSWORD', ''),
            admin_email=value('SNIPEIT_ADMIN_EMAIL', ''),
            api_timeout=float(value('SNIPEIT_API_TIMEOUT', '10')),
            browser=value('SNIPEIT_BROWSER', 'edge').lower(),
            driver_path=value('SNIPEIT_DRIVER_PATH', ''),
            headless=value('SNIPEIT_HEADLESS', 'true').lower() in {
                '1', 'true', 'yes', 'on',
            },
            ui_timeout=float(value('SNIPEIT_UI_TIMEOUT', '10')),
            db_host=value('SNIPEIT_DB_HOST', '127.0.0.1'),
            db_port=int(value('DB_HOST_PORT', '13307')),
            db_name=value('DB_DATABASE', 'snipeit'),
            db_username=value('DB_USERNAME', 'snipeit'),
            db_password=value('DB_PASSWORD', ''),
        )
