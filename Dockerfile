# =====================================================================
# SauceDemo 自动化测试 —— Docker 镜像
# 基础：python:3.12-slim
# 内置：Google Chrome (stable) + chromedriver + JDK 21 + Allure CLI 2.45.0
# 目标：与本地开发环境保持一致
# =====================================================================
FROM python:3.12-slim AS base

# --------- 系统依赖 + Chrome ---------
RUN apt-get update && apt-get install -y --no-install-recommends \
        wget gnupg2 curl ca-certificates unzip \
        fonts-liberation fonts-noto-cjk \
        libnss3 libatk1.0-0 libatk-bridge2.0-0 \
        libcups2 libxkbcommon0 libxcomposite1 libxdamage1 \
        libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 \
        libdrm2 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# --------- 安装 Google Chrome (stable) ---------
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub \
        | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] \
        http://dl.google.com/linux/chrome/deb/ stable main" \
        > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* \
    && google-chrome --version

# --------- 手动安装 chromedriver（匹配 Chrome 版本） ---------
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}') \
    && echo "Chrome version: $CHROME_VERSION" \
    && wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" \
        -O /tmp/chromedriver.zip \
    && unzip /tmp/chromedriver.zip -d /opt/ \
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
RUN wget -q "https://github.com/allure-framework/allure2/releases/download/${ALLURE_VERSION}/allure-${ALLURE_VERSION}.tgz" \
        -O /tmp/allure.tgz \
    && tar -xzf /tmp/allure.tgz -C /opt/ \
    && ln -s /opt/allure-${ALLURE_VERSION}/bin/allure /usr/local/bin/allure \
    && rm /tmp/allure.tgz \
    && allure --version

# --------- Python 依赖 ---------
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --------- 项目代码 ---------
COPY . .

# 环境变量
ENV HEADLESS=true \
    CONTAINER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# 挂载点
VOLUME ["/app/reports", "/app/logs", "/app/screenshots"]

# 默认执行：跑用例 + 生成 Allure HTML 报告
CMD ["sh", "-c", "python -m pytest -v --alluredir=reports/allure-results && allure generate reports/allure-results -o reports/allure-report --clean && echo '>>> 报告: reports/allure-report/index.html'"]