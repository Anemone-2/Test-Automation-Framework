# -*- coding: utf-8 -*-
import time
import shutil
from pathlib import Path

import pytest

from common.readyaml import ReadYamlData
from base.removefile import remove_file
from common.dingRobot import send_dd_msg
from conf.setting import dd_msg

import warnings

yfd = ReadYamlData()
_session_started_at = None


def pytest_sessionstart(session):
    """Record timing without depending on Pytest private reporter attributes."""
    global _session_started_at
    _session_started_at = time.perf_counter()


@pytest.fixture(scope="session", autouse=True)
def clear_extract():
    # 禁用HTTPS告警，ResourceWarning
    warnings.simplefilter('ignore', ResourceWarning)

    yfd.clear_yaml_data()
    remove_file("./report/temp", ['json', 'txt', 'attach', 'properties'])


def generate_test_summary(terminalreporter):
    """生成测试结果摘要字符串"""
    passed = len(terminalreporter.stats.get('passed', []))
    failed = len(terminalreporter.stats.get('failed', []))
    error = len(terminalreporter.stats.get('error', []))
    skipped = len(terminalreporter.stats.get('skipped', []))
    deselected = len(terminalreporter.stats.get('deselected', []))
    total = passed + failed + error + skipped
    duration = time.perf_counter() - _session_started_at if _session_started_at else 0.0

    summary = f"""
    自动化测试结果，通知如下，请着重关注测试失败的接口，具体执行结果如下：
    测试用例总数：{total}
    测试通过数：{passed}
    测试失败数：{failed}
    错误数量：{error}
    跳过执行数量：{skipped}
    未选择数量：{deselected}
    执行总时长：{duration}
    """
    print(summary)
    return summary


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """自动收集pytest框架执行的测试结果并打印摘要信息"""
    summary = generate_test_summary(terminalreporter)
    if dd_msg:
        send_dd_msg(summary)


def pytest_sessionfinish(session, exitstatus):
    """将环境信息写入本次 Allure 原始结果目录。"""
    allure_dir = getattr(session.config.option, 'allure_report_dir', None)
    environment_file = Path(__file__).resolve().parent / 'environment.xml'
    if allure_dir and environment_file.exists():
        target_dir = Path(allure_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(environment_file, target_dir / 'environment.xml')
