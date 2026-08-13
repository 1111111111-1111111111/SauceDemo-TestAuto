# 🍔 SauceDemo 自动化测试项目

> **目标站点**：<https://www.saucedemo.com/>
> **技术栈**：Python 3.10+ · Pytest · Selenium WebDriver · Allure · Page Object（PO 模式）
> 
> **操作系统**：Windows（本地）/ Linux（Docker / CI）
> **覆盖范围**：登录 / 商品列表 / 商品详情 / 购物车 / 结账流程
> **当前状态**：**103 条用例全部通过（全绿）**，支持数据驱动 + 关键字驱动 + Docker / GitHub Actions / Jenkins 三套 CI
> **查看 Allure 报告URL**: https://1111111111-1111111111.github.io/SauceDemo-TestAuto/allure/index.html

---

## 📁 项目结构

```
SauceDemo_autotest/
├── conftest.py                # 全局 fixtures + Allure 失败诊断钩子（截图/URL/源码）
├── pytest.ini                 # pytest 配置
├── requirements.txt           # 依赖清单
├── run.py                     # 一键运行入口
├── Makefile                   # 常用命令聚合（make setup / test / docker-up / ci-local …）
├── Dockerfile                 # Docker 镜像
├── docker-compose.yml         # 一键编排（测试容器 + Allure 预览服务 :5050）
├── .dockerignore
├── Jenkinsfile                # Jenkins 声明式流水线
├── run_docker.bat / .sh       # Windows / Linux 一键 Docker 启动脚本
├── .github/workflows/ci.yml   # GitHub Actions CI/CD
├── README.md
│
├── config/
│   └── config.py              # 全局配置
│
├── data/                      # 🟡 数据驱动层（测试数据外置）
│   ├── keywords/              #   └─ 关键字驱动用例（YAML 步骤表）
│   │   ├── smoke_buy.yaml     #       下单冒烟
│   │   └── smoke_login.yaml   #       登录冒烟
│   ├── checkout.yaml          # 结账流程参数化（2³ = 8 组合覆盖）
│   ├── login.yaml             # 登录参数化数据
│   ├── products.csv           # 商品数据（CSV 驱动）
│   └── test_data.py           # 常量（排序选项、账号等）
│
├── pages/                     # 🟢 PO 模式：页面对象层（8 个页面）
│   ├── base_page.py           # 公共基类（封装 Selenium 操作 + 纯显式等待）
│   ├── login_page.py
│   ├── products_page.py
│   ├── product_detail_page.py
│   ├── cart_page.py
│   ├── checkout_step_one_page.py
│   ├── checkout_step_two_page.py
│   └── checkout_complete_page.py
│
├── testcases/                 # 🟡 测试用例层（7 个文件，103 条用例）
│   ├── test_login.py          # 登录（成功 + 异常 + 边界）
│   ├── test_products.py       # 商品主页（排序 / 加购 / 移除 / 跳转 / 退出）
│   ├── test_product_detail.py # 商品详情（导航 / 加购 / 移除）
│   ├── test_cart.py           # 购物车（基础操作 / 移除）
│   ├── test_checkout.py       # 结账（Step One / Two / Complete）
│   ├── test_keyword_smoke.py  # 关键字驱动冒烟
│   └── test_special_users.py  # 4 种异常账户缺陷回归
│
├── utils/                     # 工具层
│   ├── app_flows.py           # 高频业务流封装（quick_login / quick_setup_cart …）
│   ├── data_loader.py         # 加载 YAML/CSV → 数据驱动（参数化）
│   ├── keyword_engine.py      # 关键字驱动引擎（YAML 步骤解释执行）
│   ├── driver.py              # WebDriver 工厂（无头 / 驱动版本检测）
│   ├── helpers.py             # 截图、Allure step 封装
│   └── logger.py              # 日志（滚动文件 + 控制台）
│
├── logs/                      # 🟢 自动生成（滚动日志 test_run.log）
├── screenshots/               # 🟢 自动生成（用例失败自动截图）
└── reports/                   # 🟢 自动生成（allure-results 原始数据 / allure-report HTML）
```

**分层依赖关系（单向，避免循环导入）：**

```
testcases（用例层） → utils（工具层） → pages（PO 层） → config / data
```

---

## 🔧 一、工具安装说明（每个工具存在的理由）

| 工具                    | 作用                                                      | 章节  |
| --------------------- | ------------------------------------------------------- | --- |
| uv                    | Python 包与虚拟环境管理（替代 pip + venv，更快）                       | 1.1 |
| 虚拟环境                  | 项目依赖隔离，不污染系统 Python                                     | 1.2 |
| 依赖包                   | selenium / pytest / allure-pytest / webdriver-manager 等 | 1.3 |
| Chrome + chromedriver | 被测浏览器与驱动                                                | 1.4 |
| Allure CLI            | 报告渲染（配合 allure-pytest 收集数据，缺一不可）                        | 1.5 |
| WSL2 + Docker Desktop | Windows 上运行容器（CI/CD 载体）                                 | 1.6 |
| Git                   | 代码版本管理，与 GitHub / Jenkins 交互                            | 1.7 |
| Jenkins               | CI/CD 调度引擎                                              | 1.8 |

### 1.1 安装 uv（Python 包与项目管理工具）

> 替代 pip + venv，统一管理项目依赖和虚拟环境，速度快

1. 下载地址：<https://github.com/astral-sh/uv/releases>
2. 下载 `uv-x86_64-pc-windows-msvc.zip`，解压到本地，如 `D:\uv\`
3. 配置系统变量：Win 菜单搜索"高级系统配置" → "环境变量" → 系统变量 `Path` → "编辑" → 添加 uv 路径（如 `D:\uv\`）
4. 验证：`uv --version` 正确输出版本号即安装成功

### 1.2 创建项目以及虚拟环境

```bash
cd [要创建项目的文件夹]
mkdir [项目名称]
cd [项目名称]
uv venv --python 3.12        # 或指定本地 Python 绝对路径
```

创建成功后项目内会出现 `.venv` 目录。激活虚拟环境：

```bash
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # Linux / macOS
```

### 1.3 依赖包一键安装

```bash
uv pip install -r requirements.txt
```

### 1.4 浏览器与驱动（本项目采用方案 A）

#### 方案 A：手动下载驱动（本项目采用）

- 使用 Chrome 浏览器，下载 `chromedriver.exe` 并加入系统 PATH
- 代码通过 `os.environ.get("CHROME_DRIVER_PATH")` 获取驱动路径，支持环境变量覆盖

#### 方案 B：webdriver-manager 自动管理

- `webdriver-manager` 已写入 `requirements.txt`
- 运行时自动下载匹配浏览器版本的驱动，无需手动配置（适合 CI / 容器）

### 1.5 安装 Allure 命令行工具（报告可视化核心）

> **存在理由**：
> 
> - `allure-pytest`（Python 包）：负责**收集**测试结果原始数据（JSON）
> - `allure` 命令行工具：负责把原始数据**渲染**为可视化 HTML 报告
> - **两者缺一不可**

1. Python 端：`uv pip install -r requirements.txt` 时已装 `allure-pytest`
2. 命令行端：
   - 下载：<https://github.com/allure-framework/allure2/releases>
   - 解压 `allure-2.xx.x.zip` 到如 `D:\tools\allure-2.45.0`
   - 把 `D:\tools\allure-2.45.0\bin` 加入系统环境变量 PATH
3. 验证：

```bash
allure --version
```

### 1.6 安装 WSL2 和 Docker Desktop

> **存在理由**：Windows 上运行 Docker 容器需要 WSL2；Jenkins 通过 Docker 执行测试，保证环境一致。

1. 启用 WSL2（PowerShell 管理员执行）：

```powershell
wsl --install
```

   重启电脑，按提示设置 Linux 用户名密码

2. 安装 Docker Desktop：
   
   - 下载：<https://www.docker.com/products/docker-desktop/>
   - 安装时勾选 "Use WSL 2 instead of Hyper-V"

3. 验证：

```bash
docker --version
docker run hello-world
```

### 1.7 安装 Git

> **存在理由**：代码版本管理，与 GitHub / Jenkins 交互。

1. 下载：<https://git-scm.com/download/win>，安装选项默认即可
2. 配置用户信息：

```bash
git config --global user.name "你的用户名"
git config --global user.email "你的邮箱"
```

3. 验证：`git --version`

### 1.8 安装 Jenkins

> **存在理由**：CI/CD 核心调度引擎：拉取 GitHub 代码  → 运行测试 → 生成报告。

1. 下载：<https://www.jenkins.io/download/>，安装 Windows 安装包（.msi）
2. 浏览器访问 <http://localhost:8080>
3. 输入初始密码（安装日志或 `C:\ProgramData\Jenkins\.jenkins\secrets\initialAdminPassword`）
4. 安装推荐插件

**Jenkins 连接 GitHub**（参考：<https://blog.csdn.net/2301_81499791/article/details/163677267>）：

1. Jenkins 安装 GitHub Integration 插件
2. GitHub 仓库 Settings → Webhooks → 添加 `http://<Jenkins地址>/github-webhook/`
3. Jenkins 配置 GitHub 凭据（Personal Access Token，类型选 secret text）

### 1.9 常用命令速查（Makefile）

```bash
make setup          # 安装依赖
make test           # 全量测试 + Allure 收集
make test-parallel  # pytest-xdist 多进程并发
make docker-up      # docker compose 一键起（含 Allure 服务）
make ci-local       # 本地模拟 CI（无头模式跑 + 生成报告）
make allure         # 生成/打开 Allure 报告
make clean          # 清理报告 / 日志 / 截图 / 缓存
```

---

## 🚀 二、运行

### 2.1 本地运行

```bash
# 激活虚拟环境后
uv run pytest                              # 全量 103 条
uv run pytest testcases/test_login.py      # 只跑登录模块
uv run pytest -m smoke                     # 只跑冒烟标记
uv run pytest -m "not flaky"               # 跳过已知不稳定用例
```

一键入口（自动清理旧报告 → 跑用例 → 生成报告 → 起 allure 服务）：

```bash
python run.py                # 跑测试 + 生成报告 + 起 allure serve
python run.py --no-serve     # 只跑测试 + 生成 HTML 报告（不起服务）
python run.py --serve        # 跳过测试，只预览已有结果
```

**注意**：必须激活当前项目虚拟环境（`.venv`）。

### 2.2 本地测试 -> Docker 打包成镜像 / 一键启动

1. 构建镜像（Dockerfile 见项目根目录）：

```bash
docker build -t saucedemo-tests:v1.0 .
# 命令末尾的 . 代表构建上下文为当前目录
```

2. 一键启动（推荐，含报告持久化 + Allure 预览服务）：

```bash
docker compose up --build
# 结果自动挂载到宿主机 ./reports ./logs ./screenshots
# Allure 报告预览：http://localhost:5050（allure-server 服务）
```

3. 或使用一键脚本 / Makefile：

```bash
run_docker.bat        # Windows
./run_docker.sh       # Linux / macOS
make docker-up        # 等价于 docker compose up --build
```

### 2.3 源码推送到 GitHub Actions（CI/CD）

> 前置条件:
> 
> + **开启GitHub Packages权限**：去仓库 `Settings` → `Actions` → `General`，在 `Workflow permissions` 下勾选 `Read and write permissions`。这是为了让工作流有权限把镜像推送到GHCR。
> 
> + **启用GitHub Pages**：去仓库 `Settings` → `Pages`，在 `Build and deployment` 下选择 `Deploy from a branch`，并选择 `gh-pages` 分支（如果还没有，git命令中创建此分支,必须执行 ）。
>   
>   ```bash
>   git branch gh-pages
>   ```

项目已内置 `.github/workflows/ci.yml`，推送到 GitHub 后自动触发：

```bash
git add .
git commit -m "feat: 自动化测试 CI"
git branch -M main
git remote add origin https://github.com/<你的用户名>/SauceDemo_autotest.git
git push -u origin main
```

**workflow 行为**：

| 触发方式                                         | 说明                                   |
| -------------------------------------------- | ------------------------------------ |
| push / pull_request（main / master / develop） | 自动运行全量测试                             |
| 手动触发（Actions 页面 Run workflow）                | 可选参数指定浏览器（chrome / firefox / edge）   |
| 定时任务                                         | 每天北京时间 06:00 自动回归（cron `0 22 * * *`） |

**CI 流程**：Checkout → 构建 Docker 镜像 → 在容器内跑测试# → 生成 Allure 报告 → 上传 artifact → 部署到 GitHub Pages。

**报告访问地址**：`https://<你的用户名>.github.io/SauceDemo_autotest/`

**需要的仓库 Secrets**（Settings → Secrets and variables → Actions）：

| Secret         | 用途                              | 是否必须       |
| -------------- | ------------------------------- | ---------- |
| `GITHUB_TOKEN` | 部署 Pages（GitHub 自动提供，无需手动创建）    | 自动         |
| `WEBHOOK_URL`  | 失败通知（钉钉 / 企业微信 / 飞书机器人 webhook） | 可选，不配则跳过通知 |

> 同一分支新提交会自动取消旧运行（`concurrency: cancel-in-progress`），避免排队浪费 CI 时长。

### 2.4 Jenkins 中执行

1. 新建 Item：Jenkins 主页 → New Item → 输入名称 → 选择 **Pipeline**
2. 配置 Pipeline：
   - Definition 选 **Pipeline script from SCM**
   - SCM 选 **Git**，填入仓库地址（GitHub）
   - 凭据选择 1.8 中配置的 GitHub 凭据
   - Script Path 填 `Jenkinsfile`
3. 保存后立即触发：**Build Now**（或 push 代码经 Webhook 自动触发）
4. 查看结果：Console Output 看执行日志；构建后可集成 Allure 插件查看报告

<img width="2879" height="1621" alt="Image" src="https://github.com/user-attachments/assets/4312f87e-1f4e-49b5-bac1-b5b5403033cc" />

---

## 📊 三、报告展示说明

报告路径：`reports/allure-report/index.html`（本地）或 GitHub Pages 地址（CI）

Allure 提供的核心视角：

* **Behaviors**：按 **Epic → Feature → Story** 三级分组（本项目核心展示方式）

**本项目 Behaviors 分级结构**（通过 `@allure.epic / feature / story` 装饰器 + conftest 动态分配实现，7 文件 112 处标注）：

每个失败用例自动附带（conftest.py `pytest_runtest_makereport` 钩子实现）：

* 失败时的**截图**（`screenshots/`，自动命名 `用例名_调用阶段_FAIL.png`）
* **页面 URL + page_source**（`allure.attach` 附加到报告，快速定位）
* **完整日志**（`logs/test_run.log`，滚动保留）
* 浏览器 session、traceback

<img width="2879" height="1529" alt="Image" src="https://github.com/user-attachments/assets/23a4fa6c-655a-4469-8e1a-50cfb53be578" />

---

## ✨ 四、项目亮点

1. **PO 模式 + 分层架构**：`testcases → utils → pages → config/data` 单向依赖，8 个页面对象复用度高；用**方法内局部导入 + TYPE_CHECKING** 解决循环引用，替代脆弱的全局导入
2. **双驱动测试**：数据驱动（YAML/CSV 参数化，结账 2³=8 组合全覆盖）+ 关键字驱动（YAML 步骤表解释执行，冒烟用例可配化）
3. **稳定性治理**：纯显式等待（禁隐式等待混用、`IMPLICIT_WAIT=0`）、无 `time.sleep` 硬编码、`pytest-rerunfailures` 对已知不稳定用例按需重试、失败自动诊断（截图 + URL + page_source 附加到 Allure）
4. **Allure 三级分级**：Epic → Feature → Story 全量覆盖（装饰器 + conftest 动态分配双保险），报告功能栏可分级展开
5. **一键 CI/CD(两种方式)**：Docker/GitHub Actions  +  GitHub/Jenkins 
6. **缺陷回归思维**：针对 SauceDemo 的 4 个异常账户做"已知缺陷回归"用例——缺陷存在则用例通过（防修复回退），缺陷被修复则用例失败（提醒更新断言）

---

## ⚠️ 五、项目运行时出现的问题（踩坑记录）

**1. Allure 路径未正确加入系统环境变量，`allure` 命令找不到**

> - 现象：`allure: command not found`
> - 解决：把 `D:\tools\allure-2.45.0\bin` 完整加入系统 PATH（**新开终端生效**，先 `allure --version` 验证）
> - 防复发：环境配置统一写入本文档 1.5；CI 中用镜像内置 allure，不依赖本机 PATH

**2. Python 3.13 下 `Pillow==10.2.0` 源码编译失败，`pip install -r requirements.txt` 整体回滚**

> - 现象：Pillow 无预编译 wheel，源码编译报错导致依赖安装全部失败（当前 `requirements.txt` 已修正为 `Pillow>=11.0`）
> - 解决：升级 Pillow 到 `>=11.0`（实测 12.x 正常）；个别包版本与 Python 版本不匹配时，先单独安装失败项
> - 防复发：`requirements.txt` 用宽松版本约束（`>=`）；新 Python 大版本先 `pip install` 冒烟验证

**3. PO 层相互全局导入导致循环引用（ImportError: cannot import name ... from partially initialized module）**

> - 现象：`cart_page` 与 `checkout_step_one_page` 互相返回对方对象，全局导入报循环导入错误
> - 解决：**方法内局部导入 + TYPE_CHECKING 类型提示**（运行时零开销，类型检查不报错）：

```python
# cart_page.py
def checkout(self) -> "CheckoutStepOnePage":
    self.click(self.CHECKOUT_BTN)
    self.wait.until(EC.url_contains("checkout-step-one"))
    from pages.checkout_step_one_page import CheckoutStepOnePage  # 延迟导入
    return CheckoutStepOnePage(self.driver)
```

> - 防复发：PO 层依赖方向必须单向；后续用 `app_flows.py` 集中编排流程，页面对象间不再互相跳转依赖

**4. fixture 链式耦合：登录 fixture 一挂，购物车 / 结账共 60 条用例全部 ERROR**

> - 现象：`logged_in_with_cart → logged_in_products → driver_instance` 链式 fixture，上游登录失败导致下游全挂
> - 解决：废弃链式 fixture，改为 **Flow 层 helper**（`quick_login` / `quick_setup_cart` / `quick_setup_checkout`），每条用例按需调用、互不牵连
> - 防复发：fixture 只负责基础设施（driver），业务前置条件交给 Flow 函数按需组装

**5. 隐式等待与显式等待混用，页面刷新后元素重新挂载导致定位超时 / 误点**

> - 现象：同一页面元素被重新渲染（如排序后商品列表刷新），隐式等待 + 显式等待叠加导致偶发超时
> - 解决：**统一纯显式等待**（`WebDriverWait + expected_conditions`），`config.py` 中 `IMPLICIT_WAIT = 0`，`driver.py` 不再强制设置隐式等待
> - 防复发：新增页面对象一律只用显式等待；代码评审检查 `implicitly_wait` / `time.sleep`

**6. 点击商品图片报 `ElementNotInteractableException`（新版 ChromeDriver）**

> - 现象：`test_click_item_image_to_detail[0~5]` 共 6 条用例全部 broken——直接 `img.click()` 被判定元素不可交互
> - 根因：SauceDemo 中 `<img>` 本身不绑定点击事件，真正可点击的是**包裹它的 `<a>` 链接**
> - 解决：先定位 `img`，再取父级 `./parent::a`，用 `EC.element_to_be_clickable` 等待后点击
> - 防复发：点击前先查 DOM 结构（`img` 的点击事件通常绑定在包裹链接上）；失败用例先看截图再改定位

**7. "性能慢"用例断言测错对象：`performance_glitch_user` 排序用例永远失败**

> - 现象：`test_performance_glitch_user_slow_sort` 断言排序耗时 > 1s，但实测排序仅 0.11~0.14s，3 次重试全败
> - 根因：SauceDemo 对该用户的人为延迟注入在**登录 / 页面加载**环节（实测 5.2s vs normal 0.23s），排序操作本身不慢——**断言测错了对象**
> - 解决：用例改为 `test_performance_glitch_user_slow_login`，计时点改为"点击登录 → inventory 页面渲染完成"
> - 防复发：写"性能慢"类用例前，先实测慢点在哪一步（登录 vs 操作），再写计时断言，避免永假失败

**8. Docker构建镜像时,加载速度过慢**

> - 现象：5373s 时进度位[5/14],速度太慢了
> - 解决：打开Docker Desktop -> Setting -> Docker Engine -> 复制粘贴(如下内容): -> 点击 Apply & Restart 重启 Docker -> 先清除缓存: docker builder prune -f -> 重新执行 docker build -t saucedemo-tests:v1.0 .
>   ```bash
>   
>         "registry-mirrors": [
>             "https://dockerproxy.com",
>             "https://docker.m.daocloud.io",
>             "https://docker.nju.edu.cn",
>             "https://docker.1panel.live"
>          ]
> - ```

**9. Jenkins 连接 GitHub 时配置 secret_text 凭证仍无法连接**

> - 现象：Jenkins 用 Personal Access Token 配 secret_text 凭据后，拉取仓库仍报认证失败
> - 解决：访问 `http://localhost:8080/script`（Groovy 控制台），带着 token 直连 `https://github.com/` 看真实报错原因（多为 token 权限不足 / 过期 / 仓库未授权），按报错逐项解决
> - 防复发：token 需勾选 `repo` 权限；排查优先看 Jenkins 系统日志 + 用 curl 先验证 token 有效性
