# 智能递归爬取使用指南

## 工作原理

智能递归爬取的核心逻辑：

```
1. 访问 KOL 主页
2. 开始循环：
   a. 获取当前页面的所有文章元素
   b. 处理新加载的文章：
      - 如果是置顶文章 → 跳过
      - 检查文章是否已存在于数据库（通过内容哈希）
      - 如果已存在 → 计数器 +1
      - 如果连续遇到 3 篇重复 → 停止爬取
      - 如果是新文章 → 立即存入数据库，计数器清零
   c. 向下滚动页面加载更多内容
   d. 如果页面无法继续滚动 → 停止
3. 返回本次新增的文章列表
```

## 核心参数

```python
BinanceSquareScraper(
    kol_username="goingsun",     # KOL 用户名
    headless=False,               # 是否无头模式
    max_articles=None,            # 最大文章数（None = 无限制）
    save_to_db=True,              # 是否保存到数据库
    db_path="binance_square.db",  # 数据库路径
    scroll_delay=1.5              # 滚动后等待时间（秒）
)
```

## 停止条件

爬虫会在以下任一条件满足时停止：

1. **遇到连续 3 篇重复文章** - 说明已经追上历史数据
2. **达到 max_articles 限制** - 如果设置了最大文章数
3. **页面滚动到底部** - 没有更多内容可加载

## 使用示例

### 1. 基本使用

```python
from scrapers import BinanceSquareScraper

# 创建爬虫实例
scraper = BinanceSquareScraper(
    kol_username="goingsun",
    save_to_db=True
)

# 执行爬取
with scraper:
    new_articles = scraper.scrape()
    print(f"获取了 {len(new_articles)} 篇新文章")
```

### 2. 限制最大文章数

```python
# 只获取最新的 20 篇文章
scraper = BinanceSquareScraper(
    kol_username="goingsun",
    max_articles=20
)

with scraper:
    articles = scraper.scrape()
```

### 3. 定时任务场景

```python
import schedule
import time

def scrape_job():
    """定时爬取任务"""
    scraper = BinanceSquareScraper(
        kol_username="goingsun",
        headless=True,  # 后台运行
        save_to_db=True
    )

    with scraper:
        new_articles = scraper.scrape()
        if new_articles:
            print(f"发现 {len(new_articles)} 篇新文章")
            # TODO: 这里可以添加通知逻辑
        else:
            print("没有新文章")

# 每小时执行一次
schedule.every(1).hours.do(scrape_job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## 数据库查询

```python
from utils.database import DatabaseManager

with DatabaseManager("binance_square.db") as db:
    # 获取总数
    count = db.get_article_count()

    # 获取特定作者的文章
    articles = db.get_articles_by_author("goingsun")

    # 获取最新的 10 篇
    recent = db.get_all_articles(limit=10)
```

## 常见问题

### Q: 如何调整重复检测的灵敏度？

A: 修改 `extract_articles_recursive()` 中的 `max_consecutive_duplicates` 参数（默认为 3）

### Q: 滚动速度太快导致内容加载不完整怎么办？

A: 增加 `scroll_delay` 参数，例如设置为 2.0 或 3.0 秒

### Q: 如何实现通知功能？

A: 在 `extract_articles_recursive()` 中找到 `# 新文章，保存到数据库` 这一段，添加通知代码。预留的 TODO 标记已在代码中。

### Q: 能否同时爬取多个 KOL？

A: 可以，为每个 KOL 创建独立的爬虫实例，或使用循环依次爬取。

## 性能优化建议

1. **使用无头模式** - 生产环境建议设置 `headless=True`
2. **合理设置滚动延迟** - 网络较慢时增加 `scroll_delay`
3. **定期清理数据库** - 删除过期的旧文章
4. **使用定时任务** - 避免频繁手动运行

## 日志查看

爬虫运行时会生成详细日志：

- 控制台输出：实时显示爬取进度
- 日志文件：`logs/binance_square_scraper.log`
- 数据库日志：`logs/database.log`

查看日志可以了解：
- 爬取了多少文章
- 跳过了多少重复文章
- 是否遇到错误
- 数据库操作详情
