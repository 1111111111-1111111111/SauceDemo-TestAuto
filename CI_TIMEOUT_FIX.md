# SauceDemo 自动化测试 CI 超时问题解决方案

> 项目：`SauceDemo_autotest` ｜ 技术栈：Python + Selenium 4.15 + pytest 9.1 + Allure
> 问题：GitHub Actions CI 中测试断言 FAILED，日志报 `TimeoutError / TimeoutException`

---

## 一、根因分析

| # | 根因 | 现象 | 证据 |
|---|------|------|------|
| 1 | **固定 10s 显式等待**（`EXPLICIT_WAIT=10`） | CI 网络延迟高，元素/URL 等待不足 | `base_page.py` 所有 `WebDriverWait(driver, 10)` |
| 2 | **URL 跳转等待一次超时即抛异常** | `wait_url_contains` 无重试，网络抖动直接 FAIL | 登录/购物车/结算跳转全走此方法 |
| 3 | **`performance_glitch_user` 人为注入 ~5s 延迟** | 登录用例 + 网络延迟叠加超过 10s 阈值 | `data/login.yaml`、`test_special_users.py` |
| 4 | **无网络连通性检查** | Runner 访问 saucedemo.com 延迟/丢包，所有用例连锁超时才暴露 | `ci.yml` 无健康检查步骤 |
| 5 | **WDM 驱动下载无超时/重试** | CI 网络抖动导致 chromedriver 下载失败 | `utils/driver.py` 直接 `.install()` |
| 6 | **无耗时监控** | 无法区分"慢用例"与"失败用例"，排查靠猜 | conftest 无计时逻辑 |

---

## 二、修改文件总览

| 文件 | 修改位置 | 内容 |
|------|---------|------|
| `config/config.py` | 超时段 | 新增 CI 自动识别 + `CI_TIMEOUT_SCALE` 放大系数；新增 `NAV_WAIT`/`RETRY_TIMES`/`RETRY_INTERVAL`/`WDM_TIMEOUT`/`WDM_RETRIES`/`WDM_VERSION`/`SLOW_TEST_THRESHOLD` |
| `utils/driver.py` | WDM 解析 / Chrome 选项 / 超时设置 | WDM 下载超时+重试；Chrome 新增 6 个稳定性参数；`set_script_timeout`；loggingPrefs 采集 console 日志 |
| `pages/base_page.py` | 新增弹性等待核心 + 改造 wait/click | `_wait_until`（超时重试）、`wait_page_ready`、`wait_any`、`scroll_into_view`；`wait_url_contains` 支持重试；`click` 支持预期 URL |
| `utils/helpers.py` | 新增工具 | `diagnose_network`（DNS/TCP/TTFB 诊断）、`retry_on_exception`（通用重试装饰器）、`record_duration`、`format_duration` |
| `conftest.py` | 会话级/用例级钩子 | 会话开始网络诊断；每用例计时+慢用例告警；会话结束输出最慢 Top10；失败 attach console 日志 |
| `.github/workflows/ci.yml` | test job | 连通性检查步骤；显式注入超时环境变量；pytest 40min 硬超时 + 单用例看门狗；执行时间监控与预警（Step Summary）；失败诊断输出；artifacts 增加 allure-results |
| `Dockerfile` | 下载步骤 / ENV | 全部 wget 加 `--timeout --tries`；chromedriver 双源回退；apt/pip 网络加固；`TZ=Asia/Shanghai`；ENV 超时默认值（含 `SHORT_WAIT`） |
| `.env.example` | 新增 | 环境变量配置示例（含本地/CI 两套参考值 + 动态阈值表 + `SHORT_WAIT`） |
| `requirements.txt` | 新增依赖 | `pytest-timeout==2.4.0`（单用例硬上限看门狗） |
| `pytest.ini` | addopts | `--timeout=240 --timeout-method=thread`（本地运行也有看门狗保护）；注释说明 reruns 与 CI workflow 的配合 |

---

## 三、代码层：等待策略优化

### 3.1 新增"弹性等待核心"（`pages/base_page.py`）

所有页面对象继承的 `BasePage` 新增 `_wait_until()`：单次显式等待超时后**自动重试**（默认 2 次、间隔 2s），网络抖动导致的瞬时超时不再直接抛异常：

```python
def _wait_until(self, condition, timeout=None, desc="", retries=None) -> bool:
    # 单次 timeout 后 sleep(RETRY_INTERVAL) 重试，最终失败才返回 False
    # 失败时自动输出 URL + document.readyState 诊断信息
```

配套方法：
- `wait_page_ready()`：等 `document.readyState == "complete"`（SPA 场景 URL 已变但 React 未挂载）
- `wait_any([...])`：多条件任一满足（柔性断言场景）
- `scroll_into_view()`：点击前滚动到可视区域，避免遮挡导致交互超时

### 3.2 改造 `wait_url_contains`（登录/购物车/结算跳转全依赖它）

```python
# 旧：一次超时即抛 TimeoutException（CI 高频误报源）
# 新：单次 timeout（默认 30s）+ 自动重试 2 次，最终失败才抛异常并截图
def wait_url_contains(self, keyword, timeout=None, retries=None) -> bool:
    ok = self._wait_until(EC.url_contains(keyword), timeout=timeout or NAV_WAIT, ...)
    if not ok:
        take_screenshot(self.driver, name=f"url_timeout_{...}")  # 截图留证
        raise TimeoutException(...)  # 附带当前 URL 诊断
```

### 3.3 改造 `click`（支持预期 URL + 滚动可见）

```python
def click(self, locator, expect_url=None):
    ele = self.find_clickable_element(locator)
    self.scroll_into_view(ele)          # 新增：避免遮挡
    try:
        ele.click()
    except TimeoutException:
        # URL 已变更 = 导航成功，只是资源慢 → 不当作失败
        # URL 未变更 → JS 兜底点击
    if expect_url:
        self.wait_url_contains(expect_url)  # 新增：点击后自动等待跳转
```

---

## 四、CI 层：GitHub Actions 优化（`.github/workflows/ci.yml`）

### 4.1 新增连通性检查步骤（测试前）

```yaml
- name: 🌐 检查被测站点连通性
  run: |
    curl -sS -o /dev/null -w \
      "HTTP %{http_code} | DNS %{time_namelookup}s | 连接 %{time_connect}s | TTFB %{time_starttransfer}s\n" \
      --connect-timeout 10 --max-time 30 https://www.saucedemo.com/ \
      || echo "::warning::saucedemo.com 连通性检查失败，测试可能大面积超时"
```

### 4.2 显式注入超时参数（不再依赖代码默认值）

```yaml
env:
  HEADLESS: "true"
  CONTAINER: "1"
  BROWSER: ${{ github.event.inputs.browser || 'chrome' }}
  CI: "true"
  CI_TIMEOUT_SCALE: "1"                    # 关闭自动放大，显式值精确控制
  EXPLICIT_WAIT: ${{ github.event.inputs.explicit_wait || '20' }}
  NAV_WAIT: "30"
  PAGE_LOAD_TIMEOUT: "60"
  RETRY_TIMES: "2"
  RETRY_INTERVAL: "2"
  SLOW_TEST_THRESHOLD: "60"
  WDM_TIMEOUT: "120"
  WDM_RETRIES: "3"
```

### 4.3 pytest 整体 40 分钟硬超时 + 单用例看门狗（pytest-timeout）

> **实测修正（2026-08-19 首轮 CI）**：49 个用例 × 每用例重开浏览器 + 失败重试，25 分钟硬超时被触发（测试步骤精确耗时 25:01 被 `timeout 1500` 杀死）。已上调至 40 分钟（2400s），仍远低于 Actions job 360 分钟上限，卡死也能兜底结束。

> **单用例看门狗（新增）**：`pytest-timeout==2.4.0` 给**每个用例**套 240s 硬上限（`--timeout=240 --timeout-method=thread`），
> 防止单个用例卡死（如某元素永远等不到）耗尽整个 job。thread 模式只杀用例线程，不拖垮 pytest 进程，
> 超时用例计入失败并可被 `--reruns` 重试。注意 2.5.0 已被 PyPI yanked，锁定 2.4.0。

```bash
timeout 2400 python -m pytest -v \
  --alluredir=reports/allure-results --clean-alluredir \
  --reruns=${{ github.event.inputs.reruns || '3' }} --reruns-delay=3 \
  --timeout=240 --timeout-method=thread \
  2>&1 | tee logs/pytest_ci.log
exit ${PIPESTATUS[0]}    # 保留 pytest 真实退出码
```

### 4.4 失败诊断输出 + Artifact 增强

- 失败时输出：pytest 输出尾部、`logs/test_run.log` 尾部、失败截图清单、最慢用例 Top10、等待超时告警统计
- Artifact `test-logs-<run_number>` 新增包含 `reports/allure-results`（失败截图+console 日志全在 Allure 报告里）
- `workflow_dispatch` 新增 `explicit_wait` / `reruns` / `short_wait` 三个输入，无需改代码即可调参

### 4.6 测试执行时间监控与预警（Step Summary）

`⏱️ 测试执行时间监控与预警` 步骤（`if: always()`，每次运行都输出到 Actions 运行摘要）：

| 监控项 | 数据来源 | 告警规则 |
|--------|---------|---------|
| pytest 总耗时 | `date +%s` 差值 | > 30min `::warning::`；> 20min `::notice::` |
| 最慢用例 Top10 | `grep "最慢用例" logs/test_run.log` | 慢用例长期占 Top 说明需优化或调参 |
| 等待超时告警次数 | `grep -c "等待超时" logs/test_run.log` | > 20 次 `::warning::` 建议调大 EXPLICIT_WAIT/NAV_WAIT/RETRY_TIMES |

同时运行测试步骤内输出 pytest 总耗时与退出码诊断（0=通过 / 1=有失败 / 2=中断 / 3=INTERNALERROR / 4=用法 / 5=无收集）。

### 4.5 退出码诊断 + 收尾加固（CI #43 排查记录）

> **实测教训（2026-08-19 CI #43）**：Allure 报告显示 **102 用例全部 passed（0 failed / 0 broken）**，
> 测试总耗时 4:09，但 job 仍 failure（运行测试步骤 4:36 失败，非超时）。
> 症状 = "用例全过但流水线失败"，说明失败发生在 **pytest 收尾阶段而非用例层**。

**根因分析（已通过本地复现缩小范围）：**

| 候选原因 | 验证方式 | 结论 |
|---|---|---|
| pytest-rerunfailures 16.4 兼容性 | 本地重建与 CI 完全一致的环境（pytest 9.1.1 + rerunfailures 16.4 + allure 2.16.0），flaky 重试用例 EXIT 0 | ✅ 排除 |
| conftest 钩子链（sessionfinish 等）逻辑缺陷 | 本地 102 个 dummy 全过用例 + 完整钩子链 + 同参数，EXIT 0 | ✅ 排除 |
| **每次 call 重复 attach 完整 test_run.log** | 102 用例 × 每次读数 MB 日志 → allure-results 膨胀数百 MB → 收尾写入 IO 异常 → INTERNALERROR（退出码 3） | 🎯 **最大嫌疑** |
| fixture teardown 异常传播 | teardown 抛异常会把用例标 error（Allure 会显示 broken），与 0 broken 矛盾 | ⚠️ 低概率，仍加固 |

**修复内容（本次提交）：**

1. **conftest.py**：
   - `pytest_runtest_makereport`：移除"每次 call 都 attach 完整日志"，改为**仅失败用例** attach 日志**尾部（限 200KB）**——这是消除 allure-results 膨胀的关键
   - `pytest_sessionfinish`：统计逻辑整体 try/except——**收尾统计异常不得影响 pytest 退出码**
   - `driver_instance` teardown：try/except 包裹 `kill_driver`——fixture teardown 异常会标 error 且连锁影响后续用例
   - `pytest_runtest_call` / `pytest_runtest_makereport`：hookwrapper yield 后代码整体 try/except——hook 异常不得覆盖用例原始结果
2. **ci.yml**：`exit ${PIPESTATUS[0]}` 前增加**退出码诊断**，区分 0=通过 / 1=有失败 / 2=中断 / 3=INTERNALERROR（重点查收尾）/ 4=用法错误 / 5=无收集，下次同类问题一眼定位

**pytest 退出码速查：** 0 全过 · 1 有失败 · 2 中断 · 3 内部错误（插件/hook 异常）· 4 用法错误 · 5 无测试收集

---

## 五、容器层：Dockerfile 优化

```dockerfile
# 1. apt 网络加固（构建阶段全局生效）
RUN echo 'Acquire::Retries "3";' > /etc/apt/apt.conf.d/80-retries \
    && echo 'Acquire::http::Timeout "30";' > /etc/apt/apt.conf.d/81-timeouts

# 2. 所有 wget 加超时+重试：Chrome 签名密钥 / chromedriver（双源回退）/ Allure（三源回退）
wget -q --tries=3 --timeout=60 -O - https://dl.google.com/...

# 3. pip 网络加固
RUN pip install --no-cache-dir --timeout 60 --retries 5 -r requirements.txt

# 4. 新增 tzdata + TZ=Asia/Shanghai（报告时间戳正确）

# 5. ENV 内置超时默认值（CI workflow 可覆盖）
ENV EXPLICIT_WAIT=20 NAV_WAIT=30 PAGE_LOAD_TIMEOUT=60 SHORT_WAIT=2 \
    RETRY_TIMES=2 RETRY_INTERVAL=2 SLOW_TEST_THRESHOLD=60 \
    WDM_TIMEOUT=120 WDM_RETRIES=3
```

---

## 六、驱动层：WebDriver Manager 优化（`utils/driver.py`）

```python
# 1. 下载超时 + 重试（环境变量注入）
os.environ.setdefault("WDM_TIMEOUT", str(WDM_TIMEOUT))
os.environ.setdefault("WDM_RETRIES", str(WDM_RETRIES))

# 2. 版本锁定（防止漂移）
if WDM_VERSION:
    os.environ["WDM_CHROME_VERSION"] = WDM_VERSION

# 3. install() 包重试（网络抖动兜底）
def _install_driver_with_retry(manager_factory, driver_name):
    # 按 WDM_RETRIES 次重试，每次 3s/6s 退避

# 4. Chrome 稳定性参数（降低容器内崩溃）
--disable-features=VizDisplayCompositor,Translate,BlinkGenPropertyTrees
--disable-software-rasterizer
--disable-extensions
--no-first-run
--no-default-browser-check
--disable-background-networking

# 5. 超时设置
driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)      # 页面加载
driver.set_script_timeout(min(PAGE_LOAD_TIMEOUT, 60)) # JS 执行（新增）

# 6. console 日志采集（失败诊断）
options.set_capability("goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"})
```

---

## 七、日志增强方案（便于后续排查）

| 位置 | 增强内容 |
|------|---------|
| `conftest.py` 会话开始 | 一次 `diagnose_network()` 输出 DNS/TCP/TTFB 延迟到日志 + Allure |
| `conftest.py` 每用例 | 计时；> `SLOW_TEST_THRESHOLD` 记 WARNING 并 attach 时长 |
| `conftest.py` 会话结束 | 输出总耗时 + **最慢用例 Top10**（CI 可直接 `grep "最慢用例"`） |
| `base_page.py` 等待失败 | 自动输出 `URL + document.readyState` |
| `conftest.py` 失败时 | attach `browser_console_logs`（JS 异常/网络错误） |
| `ci.yml` 失败时 | `grep -A 12 "最慢用例"` + `tail` 两类日志 + 截图清单 |

---

## 八、超时阈值参考值（GitHub Actions Ubuntu runner）

| 参数 | 本地开发 | CI 默认 | 网络波动剧烈时 | 说明 |
|------|---------|---------|---------------|------|
| `EXPLICIT_WAIT` | 10s | 20s | 30s | 元素出现/可点击 |
| `NAV_WAIT` | 20s | 30s | 45s | URL 跳转（登录后等最久） |
| `PAGE_LOAD_TIMEOUT` | 30s | 60s | 90s | driver.get() 页面加载 |
| `SHORT_WAIT` | 1s | 2s | 3s | 短轮询窗口（购物车角标等） |
| `RETRY_TIMES` / `RETRY_INTERVAL` | 1 / 1.5 | 2 / 2 | 3 / 3 | 等待失败重试 |
| `WDM_TIMEOUT` / `WDM_RETRIES` | 60 / 2 | 120 / 3 | 180 / 5 | 驱动下载 |
| `SLOW_TEST_THRESHOLD` | 30 | 60 | 90 | 慢用例告警线 |
| 单用例硬上限（pytest-timeout） | 240s | 240s | 240s | 看门狗，超时计失败并触发 rerun |

> **动态阈值参考**（也可用 `config.suggest_timeouts(ttfb_ms)` 读取推荐值）：
> 按 `🌐 检查被测站点连通性` 步骤实测 TTFB 选择——TTFB < 300ms 用"本地开发"列；
> 300ms~1s 用"CI 默认"列；1s~3s 用"网络波动剧烈时"列；> 3s 建议 EXPLICIT_WAIT=40 / NAV_WAIT=60 / PAGE_LOAD_TIMEOUT=120。
> 经验法则：`NAV_WAIT ≈ EXPLICIT_WAIT × 1.5`；`PAGE_LOAD_TIMEOUT ≈ EXPLICIT_WAIT × 3`；`pytest-timeout ≈ EXPLICIT_WAIT × 12`。

> 动态调整建议：CI 首次运行后看"最慢用例 Top10"，若某用例耗时接近阈值，
> 说明该环节网络开销大，可针对性调大对应等待；若大部分用例耗时 < 5s，
> 说明阈值充裕，可适当调小以加快失败反馈。

---

## 九、验证步骤

### 9.1 本地快速验证（无浏览器）

```bash
# 1) 语法检查
python -m py_compile config/config.py utils/driver.py utils/helpers.py \
  pages/base_page.py conftest.py

# 2) CI 环境配置验证（模拟）
CI=true python -c "from config.config import EXPLICIT_WAIT; print(EXPLICIT_WAIT)"  # 期望 20

# 3) 无浏览器依赖的单元测试
python -m pytest testcases/test_helpers.py -v

# 4) 单用例看门狗生效验证（pytest.ini 已内置 --timeout=240）
python -m pytest --collect-only -q   # 无 unrecognized arguments 报错即 OK
```

### 9.2 本地完整冒烟（有浏览器）

```bash
# 登录模块（含 performance_glitch_user 慢用户，验证弹性等待）
HEADLESS=true EXPLICIT_WAIT=20 NAV_WAIT=30 python -m pytest testcases/test_login.py -v

# 核心流程（登录/购物车/结算）
HEADLESS=true EXPLICIT_WAIT=20 NAV_WAIT=30 \
  python -m pytest testcases/test_cart.py testcases/test_checkout.py -v
```

### 9.3 CI 验证

```bash
git add -A && git commit -m "fix(ci): 超时治理——弹性等待+CI参数注入+网络诊断"
git push origin main
```

推送后在 Actions 页确认：
1. `🌐 检查被测站点连通性` 步骤通过（显示 HTTP 200 + TTFB）
2. `🧪 运行测试` 通过率 ≥ 95%（重试机制容错后应接近 100%）
3. 失败时 `📋 失败诊断输出` 步骤输出日志尾部和截图清单
4. Artifacts 下载 `test-logs-<run>` 查看最慢用例 Top10
5. GitHub Pages 查看 Allure 报告（含每用例耗时、浏览器 console 日志）

### 9.4 调参入口

- **不推代码调参**：仓库 → Actions → SauceDemo 自动化测试 → Run workflow → 填 `explicit_wait` / `reruns`
- **永久调整**：改 `.github/workflows/ci.yml` 中 `test` job 的 `env:`
- **本地调整**：复制 `.env.example` 为 `.env` 后修改

---

## 十、预期效果

| 指标 | 修改前 | 修改后 |
|------|--------|--------|
| 通过率 | 偶发 FAILED（网络抖动即挂） | ≥95%，重试容错后接近 100% |
| 单用例失败反馈 | 10s 即抛（误报） | 30s×3 次重试后才判失败（真实超时才失败） |
| 排查耗时 | 无日志，靠猜 | 连通性诊断 + 慢用例 Top10 + console 日志 + 截图 |
| 总执行时间 | 无保护，卡死可能耗尽 job | pytest 25min 硬上限 + job 30min |
