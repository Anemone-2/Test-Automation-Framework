import pytest

if __name__ == '__main__':
    raise SystemExit(pytest.main([
        '-q',
        './testcase/snipeit',
        '-m', 'snipeit',
        '--alluredir=./report/temp',
        '--clean-alluredir',
        '--junitxml=./report/results.xml',
    ]))
