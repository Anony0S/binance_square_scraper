# 币安广场 KOL 文章爬虫

一个功能完整的币安广场（Binance Square）KOL 文章爬虫工具，支持智能去重、定时调度和数据库存储。

## ✨ 核心特性

- **智能去重爬取**：边爬边检查数据库，遇到重复文章自动停止，避免重复抓取
- **定时自动运行**：支持定时调度器，自动定期爬取最新文章
- **数据库持久化**：SQLite 数据库存储，支持去重、查询、统计
- **浏览器自动化**：基于 DrissionPage，有效绕过 Cloudflare 等反爬虫机制
- **详细日志记录**：完整的日志系统，方便调试和监控

## 📁 项目结构

```
binance_square_scraper/
├── scrapers/                   # 爬虫模块
│   ├── base.py                # 基础爬虫类
│   └── binance_square.py      # 币安广场爬虫实现
├── utils/                      # 工具模块
│   ├── logger.py              # 日志工具
│   ├── database.py            # 数据库操作模块
│   └── scheduler.py           # 定时调度器
├── database/                   # 数据库文件目录
│   └── binance_square.db      # SQLite数据库（自动生成）
├── logs/                       # 日志文件目录
├── drission_research.py        # 调研脚本
├── main.py                     # 主程序入口
├── run_scheduler.py            # 定时调度器启动脚本
├── config.json                 # 配置文件
├── requirements.txt            # 依赖包列表
├── pyproject.toml              # 项目配置（uv）
└── README.md                   # 项目文档
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 使用 pip
pip install -r requirements.txt

# 或使用 uv（推荐，更快）
uv pip install -r requirements.txt
```

### 2. 配置项目

编辑 `config.json` 文件：

```json
{
  "kol_username": "goingsun",           // 目标 KOL 用户名
  "database": {
    "db_path": "database/binance_square.db"
  },
  "scheduler_config": {
    "enabled": true,                     // 是否启用定时任务
    "interval_hours": 1,                 // 运行间隔（小时）
    "interval_minutes": 0,               // 运行间隔（分钟）
    "headless": true,                    // 是否无头模式
    "run_immediately": false             // 启动时是否立即执行
  }
}
```

### 3. 运行方式

#### 方式一：单次手动运行

```python
from scrapers import BinanceSquareScraper

# 创建爬虫实例
scraper = BinanceSquareScraper(
    kol_username="goingsun",
    headless=False,           # 显示浏览器
    save_to_db=True           # 保存到数据库
)

# 执行爬取
with scraper:
    new_articles = scraper.scrape()
    print(f"本次获取 {len(new_articles)} 篇新文章")
```

#### 方式二：启动定时调度器

```bash
# 启动定时调度器
python run_scheduler.py

# 或使用 uv
uv run run_scheduler.py
```

调度器会按照配置的时间间隔自动运行爬虫任务。

## ⏰ 定时调度器

### 配置定时任务

在 `config.json` 中配置调度器：

```json
{
  "scheduler_config": {
    "enabled": true,              // 是否启用定时任务
    "interval_hours": 1,          // 间隔小时数
    "interval_minutes": 0,        // 间隔分钟数
    "headless": true,             // 是否使用无头模式（推荐）
    "run_immediately": false      // 启动时是否立即执行一次
  }
}
```

### 运行调度器

```bash
# 启动定时调度器
python run_scheduler.py
```

调度器启动后会显示：
- 已注册的任务列表
- 触发器配置信息
- 下次运行时间
- 实时执行日志

### 日志文件

- `logs/scheduler.log` - 调度器日志
- `logs/binance_square_scraper.log` - 爬虫执行日志
- `logs/database.log` - 数据库操作日志

### 停止调度器

在运行的终端中按 `Ctrl+C` 即可停止调度器。

### 部署建议

#### Windows 部署

**方案 1：使用 Windows 任务计划程序**

1. 创建批处理文件 `start_scheduler.bat`：
```batch
@echo off
cd /d "C:\path\to\project"
python run_scheduler.py
```

2. 在任务计划程序中创建任务：
   - 触发器：系统启动时
   - 操作：运行 `start_scheduler.bat`

**方案 2：使用 NSSM (Non-Sucking Service Manager)**

```bash
nssm install BinanceScraper "C:\Python\python.exe" "C:\path\to\project\run_scheduler.py"
nssm start BinanceScraper
```

#### Linux 部署

**使用 systemd 服务**

创建服务文件 `/etc/systemd/system/binance-scraper.service`：

```ini
[Unit]
Description=Binance Square Scheduler
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/project
ExecStart=/usr/bin/python3 /path/to/project/run_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable binance-scraper
sudo systemctl start binance-scraper
sudo systemctl status binance-scraper
```

## 💾 数据库存储

项目使用 SQLite 数据库持久化存储爬取的文章数据。

### 智能去重机制

爬虫采用**智能去重模式**，边提取边检查数据库，自动停止重复抓取：

**工作流程：**
1. 访问 KOL 主页并提取当前页面的所有文章
2. 逐篇检查文章是否已存在于数据库（通过内容哈希）
3. 如果是新文章，立即保存到数据库
4. 如果是重复文章，增加重复计数
5. 连续遇到 2 篇重复文章时，自动停止爬取
6. 自动跳过置顶文章

**核心特性：**
- ✓ 自动去重（基于 SHA256 内容哈希）
- ✓ 智能停止（遇到重复文章自动结束）
- ✓ 跳过置顶文章
- ✓ 实时显示爬取进度
- ✓ 详细的日志记录

**使用示例：**

```python
from scrapers import BinanceSquareScraper

# 创建爬虫实例
scraper = BinanceSquareScraper(
    kol_username="goingsun",
    headless=False,
    save_to_db=True,
    db_path="database/binance_square.db"
)

# 执行爬取
with scraper:
    new_articles = scraper.scrape()
    print(f"本次获取 {len(new_articles)} 篇新文章")
```

### 数据库表结构

```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash TEXT UNIQUE NOT NULL,      -- 文章唯一哈希值（SHA256）
    author TEXT NOT NULL,                    -- 作者用户名
    card_title TEXT,                         -- 文章标题
    card_description TEXT NOT NULL,          -- 文章内容
    create_time TEXT,                        -- 发布时间
    imgs TEXT,                               -- 图片列表（JSON 格式）
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 爬取时间
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- 更新时间
);

-- 索引
CREATE INDEX idx_content_hash ON articles(content_hash);
CREATE INDEX idx_author ON articles(author);
CREATE INDEX idx_create_time ON articles(create_time);
```

### 数据库 API

`DatabaseManager` 提供以下主要方法：

```python
from utils.database import DatabaseManager

# 使用上下文管理器（推荐）
with DatabaseManager("database/binance_square.db") as db:
    # 获取文章总数
    count = db.get_article_count()
    print(f"数据库中共有 {count} 篇文章")

    # 获取最新的 10 篇文章
    articles = db.get_all_articles(limit=10)

    # 根据作者查询
    author_articles = db.get_articles_by_author("goingsun")

    # 根据哈希获取文章
    article = db.get_article_by_hash(content_hash)

    # 手动插入文章
    article = {
        "author": "goingsun",
        "card_title": "文章标题",
        "card_description": "文章内容",
        "create-time": "2024-01-01 10:00:00",
        "imgs": ["url1.jpg", "url2.jpg"]
    }
    db.insert_article(article)

    # 批量插入
    db.insert_articles_batch([article1, article2, ...])
```

### 主要方法列表

- `insert_article(article)` - 插入单篇文章
- `insert_articles_batch(articles)` - 批量插入文章
- `get_article_by_hash(hash)` - 根据哈希获取文章
- `get_articles_by_author(author)` - 获取指定作者的所有文章
- `get_all_articles(limit)` - 获取所有文章
- `get_article_count()` - 获取文章总数
- `update_article(hash, updates)` - 更新文章
- `delete_article_by_hash(hash)` - 删除文章
- `generate_content_hash(article)` - 生成文章哈希值

## 📋 配置文件说明

完整的 `config.json` 配置示例：

```json
{
  "kol_username": "goingsun",                    // 目标 KOL 用户名
  "scrape_method": "auto",                       // 爬取方法（保留字段）

  "api_config": {                                // API 配置（保留字段）
    "base_url": "https://www.binance.com",
    "profile_endpoint": "",
    "articles_endpoint": "",
    "headers": {
      "User-Agent": "Mozilla/5.0...",
      "Accept": "application/json, text/plain, */*",
      "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
    },
    "params": {
      "page": 1,
      "size": 20
    }
  },

  "drission_config": {                           // DrissionPage 配置
    "headless": false,                           // 是否无头模式
    "scroll_times": 3,                           // 滚动次数（保留字段）
    "max_articles": 10,                          // 最大文章数（保留字段）
    "selectors": {                               // CSS 选择器
      "title": "[class*=\"title\"]",
      "content": "[class*=\"content\"]",
      "time": "[class*=\"time\"]"
    }
  },

  "scheduler_config": {                          // 调度器配置
    "enabled": true,                             // 是否启用定时任务
    "interval_hours": 1,                         // 间隔小时数
    "interval_minutes": 0,                       // 间隔分钟数
    "headless": true,                            // 是否无头模式
    "run_immediately": false                     // 启动时是否立即执行
  },

  "database": {                                  // 数据库配置
    "db_path": "database/binance_square.db"      // 数据库文件路径
  },

  "output": {                                    // 输出配置
    "save_to_file": true,                        // 是否保存到文件
    "file_format": "json",                       // 文件格式
    "output_dir": "data"                         // 输出目录
  },

  "advanced": {                                  // 高级配置
    "request_delay": 1,                          // 请求延迟（秒）
    "max_retries": 3,                            // 最大重试次数
    "timeout": 30,                               // 超时时间（秒）
    "enable_logging": true,                      // 是否启用日志
    "log_level": "INFO"                          // 日志级别
  }
}
```

## ⚠️ 注意事项

1. **合法合规**：确保使用符合币安服务条款，仅用于学习和研究目的
2. **频率控制**：建议设置合理的请求间隔，避免对服务器造成过大压力
3. **数据保护**：不要分享、传播或滥用爬取的数据
4. **异常处理**：做好错误重试和日志记录，及时发现和解决问题
5. **资源占用**：生产环境建议使用无头模式（`headless=True`）以减少资源占用

## ❓ 常见问题

### Q1: DrissionPage 提示浏览器启动失败？
A: 确保系统已安装 Chrome 浏览器，DrissionPage 会自动寻找 Chrome 可执行文件。

### Q2: 遇到 Cloudflare 验证？
A: 项目已集成 Cloudflare 绕过逻辑，如果仍然失败，尝试使用有头模式（`headless=False`）。

### Q3: 为什么有些文章没有被抓取到？
A: 可能是置顶文章（已自动跳过）或者页面加载不完整，可以尝试刷新后重新运行。

### Q4: 如何修改重复检测的灵敏度？
A: 在 `scrapers/binance_square.py` 的 `extract_articles()` 方法中修改 `max_consecutive_duplicates` 参数（默认为 2）。

### Q5: 数据库文件在哪里？
A: 默认位于 `database/binance_square.db`，可在配置文件中修改路径。

### Q6: 如何同时爬取多个 KOL？
A: 为每个 KOL 创建独立的爬虫实例，或使用循环依次爬取：

```python
kol_list = ["goingsun", "username2", "username3"]

for kol in kol_list:
    scraper = BinanceSquareScraper(
        kol_username=kol,
        save_to_db=True
    )
    with scraper:
        articles = scraper.scrape()
        print(f"{kol}: 获取 {len(articles)} 篇新文章")
```

## 🔧 开发调试

### 查看日志

日志文件位于 `logs/` 目录：
- `binance_square_scraper.log` - 爬虫运行日志
- `database.log` - 数据库操作日志
- `scheduler.log` - 调度器日志

### 调试模式

运行爬虫时使用有头模式和详细日志：

```python
scraper = BinanceSquareScraper(
    kol_username="goingsun",
    headless=False,           # 显示浏览器窗口
    save_to_db=True
)
```

### 数据库查询

查看数据库统计信息：

```python
from utils.database import DatabaseManager

with DatabaseManager("database/binance_square.db") as db:
    print(f"总文章数: {db.get_article_count()}")

    # 查看最新的 5 篇文章
    articles = db.get_all_articles(limit=5)
    for article in articles:
        print(f"- {article['card_title']}")
```

## 📄 许可证

本项目仅供学习和研究使用，请勿用于商业用途。

## 🙏 致谢

- [DrissionPage](https://github.com/g1879/DrissionPage) - 强大的浏览器自动化工具
- [APScheduler](https://github.com/agronholm/apscheduler) - Python 定时任务调度库
