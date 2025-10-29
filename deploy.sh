#!/bin/bash

###############################################################################
# 币安广场爬虫 - VPS 自动部署脚本
# 使用方法: sudo ./deploy.sh
###############################################################################

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    log_error "请使用 sudo 运行此脚本"
    exit 1
fi

echo "============================================================"
echo "  币安广场爬虫 - VPS 自动部署脚本"
echo "============================================================"
echo ""

# 获取当前用户
CURRENT_USER=${SUDO_USER:-$USER}
log_info "当前用户: $CURRENT_USER"

# 获取项目路径
PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)
log_info "项目路径: $PROJECT_DIR"

# 检测系统类型
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    log_info "检测到系统: $OS"
else
    log_error "无法检测系统类型"
    exit 1
fi

# 步骤 1: 安装系统依赖
echo ""
log_info "步骤 1/7: 安装系统依赖..."

if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    apt update
    apt install -y python3 python3-pip python3-venv wget curl

    # 安装 Chrome
    if ! command -v google-chrome &> /dev/null; then
        log_info "安装 Google Chrome..."
        wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
        apt install -y ./google-chrome-stable_current_amd64.deb || {
            log_warn "Chrome 安装失败，尝试安装 Chromium..."
            apt install -y chromium-browser
        }
        rm -f google-chrome-stable_current_amd64.deb
    else
        log_info "Chrome 已安装"
    fi

    # 安装中文字体
    log_info "安装中文字体..."
    apt install -y fonts-noto-cjk fonts-wqy-zenhei || log_warn "字体安装失败，继续..."

elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ]; then
    yum update -y
    yum install -y python3 python3-pip wget curl

    # 安装 Chrome
    if ! command -v google-chrome &> /dev/null; then
        log_info "安装 Google Chrome..."
        wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
        yum install -y ./google-chrome-stable_current_x86_64.rpm || {
            log_warn "Chrome 安装失败，尝试安装 Chromium..."
            yum install -y chromium
        }
        rm -f google-chrome-stable_current_x86_64.rpm
    else
        log_info "Chrome 已安装"
    fi

    # 安装中文字体
    log_info "安装中文字体..."
    yum install -y wqy-zenhei-fonts || log_warn "字体安装失败，继续..."
else
    log_error "不支持的系统类型: $OS"
    exit 1
fi

# 步骤 2: 创建虚拟环境
echo ""
log_info "步骤 2/7: 创建 Python 虚拟环境..."

cd "$PROJECT_DIR"

if [ ! -d "venv" ]; then
    sudo -u $CURRENT_USER python3 -m venv venv
    log_info "虚拟环境创建成功"
else
    log_info "虚拟环境已存在"
fi

# 步骤 3: 安装 Python 依赖
echo ""
log_info "步骤 3/7: 安装 Python 依赖..."

sudo -u $CURRENT_USER bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
log_info "依赖安装完成"

# 步骤 4: 创建必要的目录
echo ""
log_info "步骤 4/7: 创建目录结构..."

mkdir -p database logs
chown -R $CURRENT_USER:$CURRENT_USER database logs
log_info "目录创建完成"

# 步骤 5: 配置检查
echo ""
log_info "步骤 5/7: 检查配置文件..."

if [ ! -f "config.json" ]; then
    log_error "config.json 不存在，请先创建配置文件"
    exit 1
fi

# 检查是否设置了无头模式
if grep -q '"headless": false' config.json; then
    log_warn "检测到 headless 设置为 false，VPS 环境建议设置为 true"
    read -p "是否自动修改为 true? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sed -i 's/"headless": false/"headless": true/g' config.json
        log_info "已修改为无头模式"
    fi
fi

# 步骤 6: 配置 systemd 服务
echo ""
log_info "步骤 6/7: 配置 systemd 服务..."

# 创建服务文件
SERVICE_FILE="/etc/systemd/system/binance-scraper.service"

cat > $SERVICE_FILE << EOF
[Unit]
Description=Binance Square Scraper Service
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/run_scheduler.py

# 自动重启配置
Restart=always
RestartSec=10

# 日志输出
StandardOutput=append:$PROJECT_DIR/logs/service.log
StandardError=append:$PROJECT_DIR/logs/service_error.log

# 安全配置
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

log_info "服务文件已创建: $SERVICE_FILE"

# 重载 systemd
systemctl daemon-reload
log_info "systemd 配置已重载"

# 步骤 7: 启动服务
echo ""
log_info "步骤 7/7: 启动服务..."

# 启用开机自启动
systemctl enable binance-scraper
log_info "已启用开机自启动"

# 启动服务
systemctl start binance-scraper
log_info "服务已启动"

# 等待 2 秒
sleep 2

# 检查服务状态
if systemctl is-active --quiet binance-scraper; then
    log_info "✓ 服务运行正常"
else
    log_error "✗ 服务启动失败，请检查日志"
    systemctl status binance-scraper --no-pager
    exit 1
fi

# 完成
echo ""
echo "============================================================"
echo -e "${GREEN}  部署完成!${NC}"
echo "============================================================"
echo ""
echo "服务管理命令:"
echo "  查看状态: sudo systemctl status binance-scraper"
echo "  查看日志: sudo journalctl -u binance-scraper -f"
echo "  停止服务: sudo systemctl stop binance-scraper"
echo "  启动服务: sudo systemctl start binance-scraper"
echo "  重启服务: sudo systemctl restart binance-scraper"
echo ""
echo "应用日志位置:"
echo "  调度器日志: $PROJECT_DIR/logs/scheduler.log"
echo "  爬虫日志: $PROJECT_DIR/logs/binance_square_scraper.log"
echo "  服务日志: $PROJECT_DIR/logs/service.log"
echo ""
echo "数据库位置:"
echo "  $PROJECT_DIR/database/binance_square.db"
echo ""
log_info "提示: 使用 'tail -f $PROJECT_DIR/logs/scheduler.log' 实时查看日志"
