# -*- coding: utf-8 -*-
"""
一键运行入口：
- 清理 reports 目录
- 运行 pytest
- 自动生成 allure 报告
- 自动打开浏览器查看

用法：
  python run.py              # 跑测试 + 生成报告 + 起 allure 服务
  python run.py --no-serve   # 只跑测试 + 生成 HTML 报告（不起服务）
  python run.py --serve      # 跳过测试，只起 allure 服务预览已有结果
"""
import os
import shutil
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALLURE_RESULTS = os.path.join(BASE_DIR, "reports", "allure-results")
ALLURE_REPORT = os.path.join(BASE_DIR, "reports", "allure-report")


def run_command(cmd, cwd=None, shell=True):
    print(f"\n>>> {cmd}")
    p = subprocess.run(cmd, shell=shell, cwd=cwd or BASE_DIR)
    return p.returncode


def clean():
    """清理旧的报告产物"""
    shutil.rmtree(ALLURE_RESULTS, ignore_errors=True)
    os.makedirs(ALLURE_RESULTS, exist_ok=True)


def run_tests():
    """运行 pytest"""
    rc = run_command(f"{sys.executable} -m pytest -v --tb=short")
    if rc != 0:
        print("⚠️ pytest 退出码非 0（可能有失败用例），继续生成报告…")
    return rc


def generate_report():
    """生成 Allure HTML 报告"""
    print("\n📊 生成 Allure 报告…")
    rc = run_command(f"allure generate {ALLURE_RESULTS} -o {ALLURE_REPORT} --clean")
    if rc != 0:
        print("⚠️ allure 命令未找到，请确认已安装 Allure commandline 并加入 PATH")
        print("   安装方式见 README.md")
        return False
    abs_report = os.path.abspath(ALLURE_REPORT)
    print(f"\n✅ 报告已生成：file:///{abs_report.replace(os.sep, '/')}/index.html")
    return True


def serve_report():
    """起 allure serve 服务"""
    print("🚀 正在启动 allure serve …（按 Ctrl+C 退出）")
    try:
        run_command(f"allure serve {ALLURE_RESULTS}")
    except KeyboardInterrupt:
        print("\n已退出")


def main():
    args = set(sys.argv[1:])

    if "--serve" in args:
        # 只起服务预览已有结果
        serve_report()
        return

    # 1. 清理
    clean()

    # 2. 跑测试
    run_tests()

    # 3. 生成报告
    ok = generate_report()

    # 4. 起服务（除非 --no-serve）
    if ok and "--no-serve" not in args:
        serve_report()


if __name__ == "__main__":
    main()
