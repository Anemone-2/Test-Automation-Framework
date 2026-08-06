def find_status_id(client, status_type):
    response = client.get('statuslabels', params={'limit': 100})
    assert response.status_code == 200
    matches = [
        row for row in response.json()['rows']
        if row['type'] == status_type
    ]
    assert matches, f'Status label not found: {status_type}'
    return matches[0]['id']


def build_user_payload(unique_name, **overrides):
    username = overrides.pop('username', unique_name('user'))
    password = f"Snipe@{unique_name('password')[-10:]}A1"
    payload = {
        'first_name': 'Automation',
        'last_name': 'User',
        'username': username,
        'email': f'{username}@example.test',
        'password': password,
        'password_confirmation': password,
        'activated': True,
        'jobtitle': 'Test Engineer',
    }
    payload.update(overrides)
    return payload
