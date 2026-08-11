# 🍔 SauceDemo 自动化测试项目

> **目标站点**：<https://www.saucedemo.com/>
> **技术栈**：Python 3.10+ · Pytest · Selenium WebDriver · Allure · Page Object（PO 模式）
> **CI/CD**：Docker + GitHub Actions
> **覆盖范围**：登录 / 商品列表 / 商品详情 / 购物车 / 结账流程，共 **70+** 用例

---

## 📁 项目结构

```
SauceDemo_autotest/
├── .github/workflows/ci.yml  # 🆕 GitHub Actions 流水线
├── Dockerfile                # 🆕 测试环境镜像
├── docker-compose.yml        # 🆕 一键起容器 + Allure 服务
├── Makefile                  # 🆕 一键命令（make test / make docker-run）
├── run_docker.bat            # 🆕 Windows Docker 一键脚本
├── run_docker.sh             # 🆕 macOS/Linux Docker 一键脚本
├── .dockerignore
│
├── conftest.py                # 全局 fixtures + Allure 钩子
├── pytest.ini                 # pytest 配置
├── requirements.txt           # 依赖清单
├── run.py                     # 本地一键运行脚本
├── README.md
│
├── config/
│   └── config.py              # 全局配置（支持环境变量覆盖，Docker/CI 友好）
│
├── data/
│   └── test_data.py           # 测试数据
│
├── pages/                     # 🟢 PO 模式：页面对象层
│   ├── base_page.py           # 公共基类（封装 Selenium 操作）
│   ├── login_page.py
│   ├── products_page.py
│   ├── product_detail_page.py
│   ├── cart_page.py
│   ├── checkout_step_one_page.py
│   ├── checkout_step_two_page.py
│   └── checkout_complete_page.py
│
├── testcases/                 # 🟡 测试用例层
│   ├── test_login.py          # 登录（5 成功 + 5 异常 = 10）
│   ├── test_products.py       # 商品主页（4 排序 + 加购 + 移除 + 跳转 + 退出）
│   ├── test_product_detail.py # 商品详情
│   ├── test_cart.py           # 购物车
│   └── test_checkout.py       # 结账（step one / two / complete）
│
├── utils/                     # 工具层
│   ├── logger.py              # 日志（彩色 + 文件滚动）
│   ├── driver.py              # WebDriver 工厂（Selenium 4 Service API，容器适配）
│   └── helpers.py             # 截图、Allure step
│
├── logs/                      # 🟢 自动生成（滚动日志）
├── screenshots/               # 🟢 自动生成（用例失败截图）
└── reports/                   # 🟢 自动生成（allure-results / allure-report）
```

---

## 🔧 一、工具安装说明（每个工具存在的理由）

> 推荐 **Python 3.10 ~ 3.12**。所有命令在 Windows / macOS / Linux 上通用。

### 1. Python & pip
Python 是脚本语言，Selenium / Pytest 等都基于 Python。
```bash
# 自行从 python.org 下载安装，确认：
python --version
pip --version
```

### 2. 依赖包一键安装
```bash
pip install -r requirements.txt
```

| 包 | 用途 | 为什么必须 |
| --- | --- | --- |
| **selenium==4.15.2** | 浏览器自动化 SDK | Web 测试核心：驱动浏览器执行点击、输入、JS 执行；Selenium 4.x 自带 selenium-manager，已能解决大部分驱动版本问题 |
| **pytest==8.0.0** | 测试运行框架 | 比 unittest 更灵活：fixtures、参数化、markers、插件生态丰富 |
| **pytest-ordering** | 用例执行顺序控制 | 让某个用例跑在另一个之前（例如先登录再操作） |
| **allure-pytest==2.13.2** | 生成 Allure 报告 | 把 pytest 收集到的统计、步骤、截图、附件渲染成可视化 HTML 报告（Behaviors / Suites / Graphs 三大视图） |
| **colorlog==6.8.2** | 控制台彩色日志 | 控制台 DEBUG/INFO/WARNING/ERROR 一目了然，定位问题效率 ×10 |
| **webdriver-manager==4.0.1** | 自动下载浏览器驱动 | **强烈推荐**。浏览器升级后驱动版本不匹配会报错，WDM 能自动下载匹配版本，省心 |
| **pytest-rerunfailures** | 失败重跑 | 网络/动画导致的 flaky 用例可自动重试 2~3 次 |
| **pytest-html** | 可选 HTML 报告 | 离线场景备选 |
| **PyYAML** | 解析 YAML | 数据驱动场景预留 |
| **Pillow** | 图像处理 | Allure 截图附件所需 |

### 3. 浏览器与驱动（二选一）

#### ✅ 方案 A：使用 webdriver-manager 自动管理驱动（**强烈推荐**）

`webdriver-manager` 已在 requirements.txt 中，运行时会自动下载匹配版本的 chromedriver / geckodriver / msedgedriver。

#### 🛠 方案 B：手动下载驱动（公司内网 / 离线机器）
1. 查看浏览器版本：Chrome → 设置 → 关于 Chrome → 记录版本号（如 121.0.xxxxx）
2. 下载对应驱动：
   - Chrome：<https://chromedriver.chromium.org/downloads>
   - Firefox：<https://github.com/mozilla/geckodriver/releases>
   - Edge：<https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/>
3. 把 `chromedriver.exe / geckodriver.exe` 放到任意目录，将 `config/config.py` 中 `CHROME_DRIVER_PATH` 指向绝对路径。

### 4. 安装 Allure 命令行工具（**报告可视化核心**）
Allure 由两部分组成：
- Python 端：`allure-pytest`（pip 装）→ 仅负责收集报告原始数据
- 命令行端：`allure` → 负责把原始数据渲染成 HTML

#### Windows（推荐 Scoop / Chocolatey）
```powershell
# 方式 1：Scoop
scoop install allure

# 方式 2：Chocolatey
choco install allurecommandline

# 方式 3：手动（适合无包管理器环境）
# 1) 从 https://github.com/allure-framework/allure2/releases 下载 allure-2.xx.x.zip
# 2) 解压到 D:\tools\allure-2.xx.x
# 3) 把 D:\tools\allure-2.xx.x\bin 加到系统环境变量 PATH
```
验证：
```bash
allure --version
```

#### macOS
```bash
brew install allure
```

#### Linux
```bash
sudo apt-add-repository ppa:qameta/allure
sudo apt-get update
sudo apt-get install allure
```

---

## 🚀 二、运行

### 一键脚本
```bash
python run.py
```
自动清理 → 跑用例 → 生成报告 → 自动开浏览器（`allure serve`）。

### 分步执行

```bash
# 1) 跑全部用例（自动清空 allure-results）
python -m pytest -v

# 2) 指定模块
python -m pytest testcases/test_login.py -v

# 3) 按 marker 跑
python -m pytest -m login -v
python -m pytest -m "products or checkout" -v

# 4) 失败重跑（可选）
python -m pytest --reruns 2 --reruns-delay 3

# 5) 多线程 / 多进程（可选）
python -m pytest -n auto

# 6) 只跑某个用例
python -m pytest testcases/test_login.py::TestLogin::test_login_success_with_valid_user

# 7) 浏览器切换
# 编辑 config/config.py, 将 BROWSER 改为 "firefox" 或 "edge"

# 8) 生成报告
allure generate reports/allure-results -o reports/allure-report --clean

# 9) 本地起服务 (推荐)
allure serve reports/allure-results

# 10) 直接打开 HTML（双击）
reports/allure-report/index.html
```

---

## 📊 三、报告展示说明

报告路径：`reports/allure-report/index.html`

Allure 提供的核心视角：
- **Overview**：全量状态（passed / failed / broken / skipped）+ 严重程度饼图
- **Suites**：按测试类分组的列表
- **Behaviors**：按 Epic / Feature / Story 分组 ← 截图对应此处
- **Graphs**：用例依赖、重试率、耗时分布
- **Timeline**：时序图，直观看并发效率
- **Packages**：按代码包统计

每个失败用例会自动附带：
- 失败时的 **截图**（`take_screenshot`）
- **完整日志**（`logs/test_run.log`）
- 浏览器 session、traceback

---

## 🏛 四、PO 模式说明

Page Object（PO）模式是自动化测试的最佳实践之一，它把 **页面结构** 和 **测试逻辑** 解耦：

```
┌──────────────────────────────────────────┐
│              testcases/  (测试层)          │
│   test_login.py ... 只关心业务流         │
└────────────────────┬─────────────────────┘
                     │ 调用
┌────────────────────▼─────────────────────┐
│              pages/      (页面对象层)      │
│   login_page.py ... 只关心元素 + 操作     │
└────────────────────┬─────────────────────┘
                     │ 继承
┌────────────────────▼─────────────────────┐
│              BasePage   (基类)            │
│   click / input / find / wait / 截图      │
└────────────────────┬─────────────────────┘
                     │
┌────────────────────▼─────────────────────┐
│              Selenium WebDriver          │
└──────────────────────────────────────────┘
```

### PO 的好处
1. **UI 改了只改 pages/**，不需要动 testcase
2. **用例可读**：用例读起来像业务流，而不是一堆 selector
3. **复用**：登录页 → 商品页 → 详情页 → 购物车 → 结账，一步一步链式调用
4. **稳定**：所有元素查找走 BasePage 的显式等待，统一超时机制

---

## 🧪 五、用例覆盖一览（与你的 XMind 对应）

| 模块 | XMind 节点 | 对应文件 |
| --- | --- | --- |
| 登录页面 — 成功 | standard_user / problem_user / performance_glitch_user / error_user / visual_user | `test_login.py` |
| 登录页面 — 异常 | locked_out_user / 空用户名 / 空密码 / 用户名错 / 密码错 | `test_login.py` |
| 商品页面 — 排序 | Name(A→Z) / Name(Z→A) / Price(low→high) / Price(high→low) | `test_products.py` |
| 商品页面 — 加购 | 每个商品 1 个 + 随机多个 | `test_products.py` |
| 商品页面 — 移除 | 每个商品 1 个 + 随机多个 | `test_products.py` |
| 商品页面 — 详情 | 点击标题 / 点击图片 各 6 个 | `test_products.py` |
| 商品页面 — 退出 | Burger → Logout | `test_products.py` |
| 商品详情页 — 加购 / 返回 / 打开购物车 |  | `test_product_detail.py` |
| 购物车页面 — Continue / Checkout / 移除 / 点击商品 |  | `test_cart.py` |
| 结账流程 — Step one | First Name 空 / Last Name 空 / Postal 空 / 全空 / 成功 | `test_checkout.py` |
| 结账流程 — Step two | Cancel / Finish / 点商品 / 价格核对 | `test_checkout.py` |
| 结账流程 — Step three | Back Home / 购物车重置 | `test_checkout.py` |

---

## 🐳 六、Docker 一键启动

> **为什么选 Docker？**
> - **环境即代码**：Dockerfile 把 Chrome / ChromeDriver / JDK / Allure / Python 依赖全部固化，"我电脑能跑，CI 也能跑"
> - **零配置**：新人不用装 Chrome、不用装 Java、不用配 PATH，一条命令就能跑
> - **CI 友好**：GitHub Actions / Jenkins / GitLab CI 都可直接复用镜像
> - **隔离**：不污染宿主机 Python 环境

### 方式 1：一键脚本（推荐）

**Windows：**
```bash
# 双击 run_docker.bat 或命令行执行：
run_docker.bat
```

**macOS / Linux：**
```bash
chmod +x run_docker.sh
./run_docker.sh
```

脚本自动完成：清理 → 构建镜像 → 运行测试 → 生成报告 → 输出路径。

### 方式 2：docker compose（含 Allure 报告服务）

```bash
# 一键起测试容器 + Allure 报告服务
docker compose up --build

# 报告服务地址：http://localhost:5050
```

### 方式 3：手动 Docker 命令

```bash
# 构建镜像（首次约 3-5 分钟）
docker build -t saucedemo-autotest:latest .

# 运行测试
docker run --rm --shm-size=2g \
  -v "$PWD/reports:/app/reports" \
  -v "$PWD/logs:/app/logs" \
  -v "$PWD/screenshots:/app/screenshots" \
  -e HEADLESS=true \
  saucedemo-autotest:latest

# 生成报告
docker run --rm \
  -v "$PWD/reports:/app/reports" \
  --entrypoint sh \
  saucedemo-autotest:latest \
  -c "allure generate reports/allure-results -o reports/allure-report --clean"
```

### Docker 镜像内容

| 组件 | 版本 | 用途 |
| --- | --- | --- |
| Python | 3.11 slim | 运行时 |
| Google Chrome | stable | 浏览器自动化 |
| OpenJDK | 17 | Allure CLI 运行时 |
| Allure CLI | 2.27.0 | 生成测试报告 |
| selenium / pytest / allure-pytest | requirements.txt | 测试框架 |

### 环境变量（Docker / CI 覆盖）

```bash
BROWSER=chrome          # chrome / firefox / edge
HEADLESS=true           # 容器内必须 true
CONTAINER=1             # 触发 --disable-dev-shm-usage
LOG_LEVEL=INFO          # DEBUG / INFO / WARNING / ERROR
BASE_URL=https://www.saucedemo.com
```

---

## 🚀 七、GitHub Actions CI/CD

> **为什么选 GitHub Actions？**
> - **云原生 CI**：无需自建 Jenkins Agent，零运维成本
> - **与 GitHub 天然集成**：PR 直接看测试结果，状态徽章一目了然
> - **免费额度**：公共仓库无限免费，私有仓库每月 2000 分钟
> - **Allure 历史报告**：通过 GitHub Pages 永久托管，趋势图连续可查
> - **矩阵策略**：轻松实现多 Python 版本 / 多浏览器并行

### 配置文件

```
.github/workflows/ci.yml
```

### 触发条件

- `push` 到 main / master / develop
- `pull_request` 到 main / master
- 手动触发（可指定浏览器）
- 定时：每天北京时间 06:00 自动回归

### 流水线步骤

```
Checkout → Python 3.11 → JDK 17 → Allure CLI → Chrome →
装依赖 → 跑测试 → 拉历史 → 生成报告 → 上传 artifact → 部署 GitHub Pages
```

### 使用方式

1. **把项目推到 GitHub 仓库**
2. 进入仓库 Settings → Pages → Source 选 `gh-pages` 分支
3. 下次 push 到 main 后，Actions 自动跑
4. Allure 报告地址：`https://<你的用户名>.github.io/<仓库名>/`

### 本地模拟 CI

```bash
make ci-local
# 或手动：
HEADLESS=true CONTAINER=1 python -m pytest -v --clean-alluredir
allure generate reports/allure-results -o reports/allure-report --clean
```

### 失败通知（可选）

在仓库 Settings → Secrets 添加 `WEBHOOK_URL`（钉钉 / 飞书 / 企业微信机器人），测试失败时自动推送通知。

---

## ❓ 八、常见问题排查（FAQ）

| 现象 | 解决 |
| --- | --- |
| `selenium.common.exceptions.WebDriverException: unknown error: cannot find Chrome binary` | 没装 Chrome 浏览器，或浏览器不是默认路径。装 Chrome 或改 `BROWSER = "edge"` |
| `chromedriver 版本与 Chrome 不匹配` | 升级 selenium 到 4.10+，或用 `webdriver-manager`；手动驱动则去 chromedriver.chromium.org 下载匹配版本 |
| Allure 命令 `allure generate` 报 "allure 不是内部命令" | 第 4 步没把 allure bin 加到 PATH，重启终端 |
| 报告打开后没有用例 | `--alluredir` 没配置好。看 `pytest.ini` 已经写了 `--alluredir=reports/allure-results` |
| 部分用例 flaky（偶发失败） | 加 `--reruns 2`，或调大 `EXPLICIT_WAIT` |
| 速度太慢 | `pytest-xdist` 多线程：`pip install pytest-xdist && pytest -n auto` |
| Chrome 控制台一直显示 "正受自动化软件控制" | 已通过 `excludeSwitches` 屏蔽；如果残留，是浏览器版本较新，可忽略 |
| 想跑无头模式（CI / 服务器） | 修改 `config/config.py` 的 `HEADLESS = True`，或设环境变量 `HEADLESS=true` |
| Windows 上 chromedriver.exe 提示 "未知发布者" | 右键 → 属性 → 解除锁定，或以管理员运行 |
| Docker 内 Chrome 崩溃 | 确保 `--shm-size=2g`，或代码已自动启用 `--disable-dev-shm-usage` |
| `executable_path` 警告 | Selenium 4 已废弃该参数，本项目已改用 `service=Service(...)` |
| GitHub Actions Allure 历史不连续 | 确认 gh-pages 分支存在且 Pages 已开启 |

---

## 🍪 九、附：SauceDemo 自带的官方测试账号

| 用户名 | 密码 | 说明 |
| --- | --- | --- |
| `standard_user` | secret_sauce | 正常用户 |
| `locked_out_user` | secret_sauce | 已锁定，登录会被拒 |
| `problem_user` | secret_sauce | 会有 UI bug（排序/图片错乱） |
| `performance_glitch_user` | secret_sauce | 有意减速 5s，验证性能 |
| `error_user` | secret_sauce | 操作时常触发服务端 500 |
| `visual_user` | secret_sauce | 视觉对账验证 |

来源：<https://www.saucedemo.com/> 页面上明确列出。

---

> 🤖 这个项目以 **端测测** 的姿态编写 —— 一切围绕 “让团队敢发布” 这个信条展开。
> 如果你觉得有帮助，欢迎二次扩展：Jenkins / GitHub Actions 集成、参数化多浏览器、加压测试、移动端 WebView 等。
