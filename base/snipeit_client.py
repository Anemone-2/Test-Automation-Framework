import json
from urllib.parse import urljoin

import allure
import requests

from common.sensitive_data import redact_sensitive


_USE_CONFIGURED_TOKEN = object()


class SnipeItClient:
    """Small REST client for the locally deployed Snipe-IT API."""

    def __init__(self, settings, token=_USE_CONFIGURED_TOKEN):
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'Test-Automation-Framework/0.1',
        })
        effective_token = settings.api_token if token is _USE_CONFIGURED_TOKEN else token
        if effective_token:
            self.session.headers['Authorization'] = f'Bearer {effective_token}'

    def close(self):
        self.session.close()

    def request(self, method, path, **kwargs):
        url = urljoin(f'{self.settings.base_url}/', f'api/v1/{path.lstrip("/")}')
        timeout = kwargs.pop('timeout', self.settings.api_timeout)
        report_headers = dict(self.session.headers)
        report_headers.update(kwargs.get('headers') or {})
        report_request = {
            'method': method.upper(),
            'url': url,
            'headers': redact_sensitive(report_headers),
            'params': redact_sensitive(kwargs.get('params')),
            'json': redact_sensitive(kwargs.get('json')),
        }
        allure.attach(
            json.dumps(report_request, ensure_ascii=False, indent=2),
            name='API request',
            attachment_type=allure.attachment_type.JSON,
        )

        response = self.session.request(
            method=method,
            url=url,
            timeout=timeout,
            **kwargs,
        )
        try:
            response_body = redact_sensitive(response.json())
            rendered_body = json.dumps(response_body, ensure_ascii=False, indent=2)
            attachment_type = allure.attachment_type.JSON
        except ValueError:
            rendered_body = response.text
            attachment_type = allure.attachment_type.TEXT

        allure.attach(
            rendered_body,
            name=f'API response ({response.status_code})',
            attachment_type=attachment_type,
        )
        return response

    def get(self, path, **kwargs):
        return self.request('GET', path, **kwargs)

    def post(self, path, **kwargs):
        return self.request('POST', path, **kwargs)

    def patch(self, path, **kwargs):
        return self.request('PATCH', path, **kwargs)

    def delete(self, path, **kwargs):
        return self.request('DELETE', path, **kwargs)
