import os
import shutil
import urllib.error
import urllib.request

import pytest
import webbrowser
from conf.setting import REPORT_TYPE


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def ensure_mock_server():
    try:
        with urllib.request.urlopen('http://127.0.0.1:8787/index', timeout=2):
            return
    except (urllib.error.URLError, TimeoutError):
        print('Mock 服务未启动，请先运行：')
        print(r'cd mock_server\api_server\base')
        print(r'python flask_service.py')
        raise SystemExit(1)

if __name__ == '__main__':
    os.chdir(PROJECT_ROOT)
    ensure_mock_server()

    if REPORT_TYPE == 'allure':
        exit_code = pytest.main(
            ['-s', '-v', '--alluredir=./report/temp', './testcase', '--clean-alluredir',
             '--junitxml=./report/results.xml'])
        if exit_code != pytest.ExitCode.OK:
            raise SystemExit(exit_code)
        if shutil.which('allure') is None:
            print('测试已通过，但未找到 Allure CLI。可手动执行 allure serve ./report/temp')
            raise SystemExit(1)
        raise SystemExit(os.system('allure serve ./report/temp'))

    elif REPORT_TYPE == 'tm':
        exit_code = pytest.main(['-vs', '--pytest-tmreport-name=testReport.html',
                                 '--pytest-tmreport-path=./report/tmreport'])
        if exit_code != pytest.ExitCode.OK:
            raise SystemExit(exit_code)
        webbrowser.open_new_tab(os.getcwd() + '/report/tmreport/testReport.html')
