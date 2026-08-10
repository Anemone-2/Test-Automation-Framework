import shutil
import time
from pathlib import Path

_session_started_at = None


def pytest_sessionstart(session):
    """Record timing without depending on Pytest private reporter attributes."""
    global _session_started_at
    _session_started_at = time.perf_counter()


def generate_test_summary(terminalreporter):
    """生成当前 Snipe-IT 测试会话的结果摘要。"""
    passed = len(terminalreporter.stats.get('passed', []))
    failed = len(terminalreporter.stats.get('failed', []))
    error = len(terminalreporter.stats.get('error', []))
    skipped = len(terminalreporter.stats.get('skipped', []))
    deselected = len(terminalreporter.stats.get('deselected', []))
    total = passed + failed + error + skipped
    duration = time.perf_counter() - _session_started_at if _session_started_at else 0.0

    summary = (
        '\nSnipe-IT 自动化测试结果：\n'
        f'用例总数：{total}\n'
        f'通过：{passed}\n'
        f'失败：{failed}\n'
        f'错误：{error}\n'
        f'跳过：{skipped}\n'
        f'未选择：{deselected}\n'
        f'执行总时长：{duration:.2f} 秒\n'
    )
    print(summary)
    return summary


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """在终端输出独立于外部通知服务的测试摘要。"""
    generate_test_summary(terminalreporter)


def pytest_sessionfinish(session, exitstatus):
    """将环境信息写入本次 Allure 原始结果目录。"""
    allure_dir = getattr(session.config.option, 'allure_report_dir', None)
    environment_file = Path(__file__).resolve().parent / 'environment.xml'
    if allure_dir and environment_file.exists():
        target_dir = Path(allure_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(environment_file, target_dir / 'environment.xml')
