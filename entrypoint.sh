#!/bin/bash
set -e

echo "========================================="
echo "SauceDemo 自动化测试容器"
echo "测试套件: ${TEST_SUITE:-smoke}"
echo "测试标记: ${TEST_MARKER:-无}"
echo "========================================="

# 根据 TEST_SUITE 环境变量决定执行哪些测试
case ${TEST_SUITE:-"smoke"} in
  "smoke")
    echo ">>> 执行冒烟测试"
    pytest -v -m smoke "$@" || EXIT_CODE=$?
    ;;
  "regression")
    echo ">>> 执行回归测试"
    pytest -v -m regression "$@" || EXIT_CODE=$?
    ;;
  "all")
    echo ">>> 执行全部测试"
    pytest -v "$@" || EXIT_CODE=$?
    ;;
  "custom")
    echo ">>> 执行自定义测试: ${TEST_MARKER}"
    pytest -v -m "${TEST_MARKER}" "$@" || EXIT_CODE=$?
    ;;
  *)
    echo ">>> 执行默认测试 (smoke)"
    pytest -v -m smoke "$@" || EXIT_CODE=$?
    ;;
esac

# 无论测试是否通过，生成 Allure 报告
echo "========================================="
echo "生成 Allure 报告..."
echo "========================================="
allure generate reports/allure-results -o reports/allure-report --clean

echo "========================================="
echo "报告已生成: /app/reports/allure-report/index.html"
echo "========================================="

# 退出码（测试失败时仍生成报告，但返回失败状态）
if [ -n "$EXIT_CODE" ] && [ "$EXIT_CODE" -ne 0 ]; then
    echo ">>> 部分测试失败 (退出码: $EXIT_CODE)"
    exit $EXIT_CODE
fi

echo ">>> 所有测试通过 ✅"
exit 0