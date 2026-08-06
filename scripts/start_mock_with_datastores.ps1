$ErrorActionPreference = 'Stop'
$env:DATA_STORES_ENABLED = 'true'
python "$PSScriptRoot\..\mock_server\api_server\base\flask_service.py"
