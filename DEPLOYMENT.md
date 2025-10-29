# VPS 部署指南

本文档介绍如何将币安广场爬虫项目部署到 Linux VPS 上。

## 前置要求

- Linux VPS (Ubuntu 20.04+ / Debian 11+ / CentOS 8+)
- SSH 访问权限
- Root 或 sudo 权限
- 至少 2GB RAM
- 至少 10GB 可用磁盘空间

## 部署步骤

### 1. 连接到 VPS

```bash
ssh your_username@your_vps_ip
```

### 2. 更新系统并安装基础依赖

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git wget curl

# CentOS/RHEL
sudo yum update -y
sudo yum install -y python3 python3-pip git wget curl
```

### 3. 安装 Chrome/Chromium 浏览器

DrissionPage 需要 Chrome 浏览器才能运行。

#### Ubuntu/Debian:

```bash
# 安装 Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb

# 或者安装 Chromium (更轻量)
sudo apt install -y chromium-browser
```

#### CentOS/RHEL:

```bash
# 安装 Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
sudo yum install -y ./google-chrome-stable_current_x86_64.rpm

# 或者安装 Chromium
sudo yum install -y chromium
```

### 4. 安装中文字体 (可选，但推荐)

```bash
# Ubuntu/Debian
sudo apt install -y fonts-noto-cjk fonts-wqy-zenhei

# CentOS/RHEL
sudo yum install -y wqy-zenhei-fonts
```

### 5. 克隆项目代码

```bash
# 创建项目目录
mkdir -p ~/projects
cd ~/projects

# 克隆代码 (如果使用 Git)
git clone <your_git_repo_url> binance-scraper
cd binance-scraper

# 或者直接上传项目文件
# 可以使用 scp 命令从本地上传:
# scp -r /path/to/local/project your_username@your_vps_ip:~/projects/binance-scraper
```

### 6. 安装 Python 依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

### 7. 配置项目

编辑 `config.json` 文件，确保配置正确:

```bash
nano config.json
```

重要配置项:

```json
{
  "scheduler_config": {
    "enabled": true,
    "interval_hours": 1,
    "interval_minutes": 0,
    "headless": true,          // 必须设置为 true (无头模式)
    "run_immediately": false
  }
}
```

**注意**: 在 VPS 上必须使用无头模式 (`headless: true`)。

### 8. 测试运行

先手动测试爬虫是否正常工作:

```bash
# 激活虚拟环境
source venv/bin/activate

# 测试运行
python run_scheduler.py
```

如果遇到浏览器相关错误，检查:
- Chrome 是否正确安装: `google-chrome --version` 或 `chromium-browser --version`
- 是否有必要的依赖库

按 `Ctrl+C` 停止测试。

### 9. 设置为系统服务 (推荐)

使用 systemd 将爬虫设置为后台服务，开机自启动。

#### 方法 A: 使用自动部署脚本

```bash
# 运行部署脚本
chmod +x deploy.sh
sudo ./deploy.sh
```

#### 方法 B: 手动配置

创建 systemd 服务文件:

```bash
sudo nano /etc/systemd/system/binance-scraper.service
```

复制以下内容 (替换路径和用户名):

```ini
[Unit]
Description=Binance Square Scraper Service
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/projects/binance-scraper
Environment="PATH=/home/your_username/projects/binance-scraper/venv/bin"
ExecStart=/home/your_username/projects/binance-scraper/venv/bin/python run_scheduler.py
Restart=always
RestartSec=10
StandardOutput=append:/home/your_username/projects/binance-scraper/logs/service.log
StandardError=append:/home/your_username/projects/binance-scraper/logs/service_error.log

[Install]
WantedBy=multi-user.target
```

启动服务:

```bash
# 重载 systemd 配置
sudo systemctl daemon-reload

# 启用开机自启动
sudo systemctl enable binance-scraper

# 启动服务
sudo systemctl start binance-scraper

# 查看服务状态
sudo systemctl status binance-scraper
```

### 10. 服务管理命令

```bash
# 查看服务状态
sudo systemctl status binance-scraper

# 启动服务
sudo systemctl start binance-scraper

# 停止服务
sudo systemctl stop binance-scraper

# 重启服务
sudo systemctl restart binance-scraper

# 查看服务日志
sudo journalctl -u binance-scraper -f

# 查看最近 100 行日志
sudo journalctl -u binance-scraper -n 100

# 查看应用日志
tail -f logs/scheduler.log
tail -f logs/binance_square_scraper.log
```

## 方案二: 使用 Screen/Tmux (简单但不推荐用于生产环境)

如果不想配置 systemd，可以使用 screen 或 tmux:

```bash
# 安装 screen
sudo apt install -y screen  # Ubuntu/Debian
# sudo yum install -y screen  # CentOS

# 创建新会话
screen -S binance-scraper

# 激活虚拟环境并运行
cd ~/projects/binance-scraper
source venv/bin/activate
python run_scheduler.py

# 按 Ctrl+A 然后按 D 来脱离会话 (程序继续运行)

# 重新连接会话
screen -r binance-scraper

# 查看所有会话
screen -ls
```

## 方案三: 使用 Docker (高级)

如果你熟悉 Docker，可以使用容器化部署:

```bash
# 使用项目中的 Dockerfile
docker build -t binance-scraper .
docker run -d --name binance-scraper \
  -v $(pwd)/database:/app/database \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config.json:/app/config.json \
  --restart unless-stopped \
  binance-scraper
```

## 监控和维护

### 1. 定期检查日志

```bash
# 查看调度器日志
tail -f ~/projects/binance-scraper/logs/scheduler.log

# 查看爬虫日志
tail -f ~/projects/binance-scraper/logs/binance_square_scraper.log

# 查看数据库日志
tail -f ~/projects/binance-scraper/logs/database.log
```

### 2. 检查数据库

```bash
cd ~/projects/binance-scraper

# 使用 sqlite3 查看数据库
sqlite3 database/binance_square.db

# 在 sqlite3 中执行查询
SELECT COUNT(*) FROM articles;
SELECT * FROM articles ORDER BY create_time DESC LIMIT 5;
.quit
```

### 3. 设置日志轮转 (防止日志文件过大)

创建 logrotate 配置:

```bash
sudo nano /etc/logrotate.d/binance-scraper
```

添加以下内容:

```
/home/your_username/projects/binance-scraper/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 your_username your_username
}
```

### 4. 设置定期备份数据库

创建备份脚本:

```bash
nano ~/backup_db.sh
```

内容:

```bash
#!/bin/bash
BACKUP_DIR=~/backups/binance-scraper
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
cp ~/projects/binance-scraper/database/binance_square.db \
   $BACKUP_DIR/binance_square_$DATE.db

# 只保留最近 7 天的备份
find $BACKUP_DIR -name "binance_square_*.db" -mtime +7 -delete
```

添加到 crontab:

```bash
chmod +x ~/backup_db.sh
crontab -e

# 添加每天凌晨 3 点备份
0 3 * * * ~/backup_db.sh
```

## 故障排查

### 问题 1: Chrome 浏览器启动失败

```bash
# 检查 Chrome 是否安装
google-chrome --version
# 或
chromium-browser --version

# 安装缺失的依赖
sudo apt install -y libnss3 libgconf-2-4 libxss1 libasound2
```

### 问题 2: 权限问题

```bash
# 确保项目目录权限正确
cd ~/projects
sudo chown -R $USER:$USER binance-scraper
chmod -R 755 binance-scraper
```

### 问题 3: 服务无法启动

```bash
# 查看详细错误信息
sudo journalctl -u binance-scraper -n 50 --no-pager

# 检查服务配置
sudo systemctl status binance-scraper

# 手动测试运行
cd ~/projects/binance-scraper
source venv/bin/activate
python run_scheduler.py
```

### 问题 4: 内存不足

如果 VPS 内存较小，可能导致 Chrome 崩溃:

```bash
# 在 config.json 中减少间隔时间
# 或者添加 swap 空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久生效
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 安全建议

1. 使用非 root 用户运行服务
2. 配置防火墙只开放必要端口
3. 定期更新系统和依赖包
4. 不要在配置文件中存储敏感信息
5. 定期备份数据库文件
6. 监控磁盘空间使用情况

## 更新部署

当代码有更新时:

```bash
# 停止服务
sudo systemctl stop binance-scraper

# 更新代码
cd ~/projects/binance-scraper
git pull  # 如果使用 git

# 更新依赖
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 重启服务
sudo systemctl start binance-scraper

# 查看状态
sudo systemctl status binance-scraper
```

## 性能优化建议

1. 使用 SSD VPS 提升数据库性能
2. 合理设置爬取间隔，避免频繁请求
3. 启用无头模式减少资源占用
4. 定期清理旧日志文件
5. 使用数据库索引优化查询

## 资源需求参考

- 最小配置: 1 核 CPU, 2GB RAM, 10GB 硬盘
- 推荐配置: 2 核 CPU, 4GB RAM, 20GB 硬盘
- 网络: 稳定的互联网连接

## 常见 VPS 提供商

- Vultr: https://www.vultr.com
- DigitalOcean: https://www.digitalocean.com
- Linode: https://www.linode.com
- 阿里云: https://www.aliyun.com
- 腾讯云: https://cloud.tencent.com

## 技术支持

如遇到问题，请检查:
1. 系统日志: `sudo journalctl -u binance-scraper`
2. 应用日志: `logs/` 目录下的日志文件
3. Chrome 是否正常工作
4. 网络连接是否正常
