# =====================================================================
# SauceDemo 自动化测试 —— Docker 镜像（超时治理版）
# 基础：python:3.12-slim
# 内置：Google Chrome (stable) + chromedriver + JDK 21 + Allure CLI 2.45.0
# 目标：与本地开发环境保持一致
#
# 超时治理（本版本新增）：
#   1. 所有网络下载（Chrome / chromedriver / Allure / pip）均带 --timeout + 重试
#   2. apt-get 增加 Acquire::Retries，避免镜像构建阶段偶发网络抖动失败
#   3. 增加 tzdata，Allure 报告时间戳使用正确时区
# =====================================================================
FROM python:3.12-slim AS base

# apt 网络加固：自动重试 3 次，超时上限 30s
RUN echo 'Acquire::Retries "3";' > /etc/apt/apt.conf.d/80-retries \
    && echo 'Acquire::http::Timeout "30";' > /etc/apt/apt.conf.d/81-timeouts

# --------- 系统依赖 + Chrome ---------
RUN apt-get update && apt-get install -y --no-install-recommends \
        wget gnupg2 curl ca-certificates unzip \
        fonts-liberation fonts-noto-cjk \
        libnss3 libatk1.0-0 libatk-bridge2.0-0 \
        libcups2 libxkbcommon0 libxcomposite1 libxdamage1 \
        libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 \
        libdrm2 libxshmfence1 tzdata \
    && rm -rf /var/lib/apt/lists/*

# --------- 安装 Google Chrome (stable) ---------
RUN wget -q --tries=3 --timeout=60 -O - https://dl.google.com/linux/linux_signing_key.pub \
        | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] \
        http://dl.google.com/linux/chrome/deb/ stable main" \
        > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* \
    && google-chrome --version

# --------- 手动安装 chromedriver（匹配 Chrome 版本，带超时与重试） ---------
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}') \
    && echo "Chrome version: $CHROME_VERSION" \
    && for url in \
        "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" \
        "https://googlechromelabs.github.io/chrome-for-testing/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" \
    ; do \
        echo ">>> 尝试下载 chromedriver: ${url}"; \
        if wget -q --tries=3 --timeout=90 -O /tmp/chromedriver.zip "${url}"; then \
            echo ">>> chromedriver 下载成功"; \
            break; \
        fi; \
        echo ">>> 下载失败，尝试下一个源"; \
    done; \
    unzip /tmp/chromedriver.zip -d /opt/ \
    && ln -s /opt/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && rm /tmp/chromedriver.zip \
    && chromedriver --version

# --------- 安装 JDK 21（与你本地一致） ---------
# OpenJDK 21 在 Debian 官方源中已支持
RUN apt-get update && apt-get install -y --no-install-recommends \
        openjdk-21-jre-headless \
    && rm -rf /var/lib/apt/lists/* \
    && java -version

# --------- 安装 Allure CLI 2.45.0（与你本地版本一致） ---------
ARG ALLURE_VERSION=2.45.0
# 注意：GitHub Releases 直连在国内网络经常超时（wget exit code 4 = 网络故障）。
# GitHub release 的 allure-2.x.x.tgz 与 Maven 仓库的 allure-commandline-2.x.x.tgz 是同一份产物，
# 因此优先从阿里云 Maven 镜像下载，失败则回退 Maven Central，最后再试 GitHub。
#RUN wget -q "https://github.com/allure-framework/allure2/releases/download/${ALLURE_VERSION}/allure-${ALLURE_VERSION}.tgz" \
#            -O /tmp/allure.tgz \
#	&& tar -xzf /tmp/allure.tgz -C /opt/ \

RUN for url in \
        "https://maven.aliyun.com/repository/central/io/qameta/allure/allure-commandline/${ALLURE_VERSION}/allure-commandline-${ALLURE_VERSION}.tgz" \
        "https://repo1.maven.org/maven2/io/qameta/allure/allure-commandline/${ALLURE_VERSION}/allure-commandline-${ALLURE_VERSION}.tgz" \
        "https://github.com/allure-framework/allure2/releases/download/${ALLURE_VERSION}/allure-${ALLURE_VERSION}.tgz" \
    ; do \
        echo ">>> 尝试下载 Allure: ${url}"; \
        if wget -q --tries=3 --timeout=60 -O /tmp/allure.tgz "${url}"; then \
            echo ">>> 下载成功: ${url}"; \
            break; \
        fi; \
        echo ">>> 下载失败，尝试下一个源"; \
    done; \
    tar -xzf /tmp/allure.tgz -C /opt/ \
	&& ln -s /opt/allure-${ALLURE_VERSION}/bin/allure /usr/local/bin/allure \
	&& rm /tmp/allure.tgz \
	&& allure --version



# --------- Python 依赖（pip 网络加固：超时 60s、重试 5 次） ---------
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 60 --retries 5 -r requirements.txt

# --------- 项目代码 ---------
COPY . .

# 环境变量
ENV HEADLESS=true \
    CONTAINER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    TZ=Asia/Shanghai \
    # ---- 超时治理默认值（CI workflow 可通过环境变量覆盖）----
    EXPLICIT_WAIT=20 \
    NAV_WAIT=30 \
    PAGE_LOAD_TIMEOUT=60 \
    RETRY_TIMES=2 \
    RETRY_INTERVAL=2 \
    SLOW_TEST_THRESHOLD=60 \
    WDM_TIMEOUT=120 \
    WDM_RETRIES=3

# 挂载点
VOLUME ["/app/reports", "/app/logs", "/app/screenshots"]

# 默认执行：跑用例 + 生成 Allure HTML 报告
CMD ["sh", "-c", "python -m pytest -v --alluredir=reports/allure-results && allure generate reports/allure-results -o reports/allure-report --clean && echo '>>> 报告: reports/allure-report/index.html'"]