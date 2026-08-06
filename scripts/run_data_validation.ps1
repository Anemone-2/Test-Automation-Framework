$ErrorActionPreference = 'Stop'
python -m pytest -s -v -m integration --alluredir=.\report\temp --clean-alluredir .\testcase
