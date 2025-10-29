FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖和 Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p database logs data

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 暴露端口 (如果需要)
# EXPOSE 8000

# 运行命令
CMD ["python", "run_scheduler.py"]
