# 飞书通知功能使用指南

本项目支持将新文章通知发送到飞书机器人，支持两种方式：

1. **Webhook 方式**（推荐）：简单快捷，无需应用认证
2. **API 方式**：功能更强大，需要创建飞书应用

## 方式一：Webhook（推荐）

### 1. 创建飞书群机器人

1. 在飞书中创建一个群组（或使用现有群组）
2. 点击群设置 → 群机器人 → 添加机器人 → 自定义机器人
3. 设置机器人名称和描述
4. 复制生成的 **Webhook 地址**
5. （可选）配置安全设置，添加签名验证

### 2. 配置项目

编辑 `config.json` 文件：

```json
{
  "feishu": {
    "enabled": true,
    "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxxx"
  }
}
```

### 3. 测试通知

运行测试脚本：

```bash
python test_feishu.py
```

选择 `1` 测试 Webhook 方式，如果配置正确，你会在飞书群中收到测试消息。

### 4. 启动爬虫

配置完成后，正常运行爬虫或定时调度器即可：

```bash
# 单次运行
python main.py

# 启动定时调度器
python run_scheduler.py
```

当有新文章时，会自动发送通知到飞书群。

---

## 方式二：API（高级）

### 1. 创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 在「凭证与基础信息」中获取 `App ID` 和 `App Secret`
4. 在「权限管理」中添加权限：
   - `im:message`（发送消息）
   - `im:message:send_as_bot`（以应用身份发消息）
5. 发布应用版本并在企业内启用

### 2. 获取接收者 ID

#### 获取群聊 ID（chat_id）

1. 将机器人添加到目标群聊
2. 使用飞书开放平台的 API 调试工具或通过代码获取群聊列表
3. 找到目标群聊的 `chat_id`

#### 获取用户 ID（user_id/open_id）

可以通过飞书管理后台或 API 获取用户的 `open_id` 或 `user_id`

### 3. 配置项目

编辑 `config.json` 文件：

```json
{
  "feishu": {
    "enabled": true,
    "app_id": "cli_xxxxxxxxxxxxxxxx",
    "app_secret": "xxxxxxxxxxxxxxxxxxxxxxxx",
    "receive_id": "oc_xxxxxxxxxxxxxxxx",
    "receive_id_type": "chat_id"
  }
}
```

**receive_id_type 说明：**
- `chat_id`：群聊 ID
- `open_id`：用户 Open ID
- `user_id`：用户 ID
- `email`：用户邮箱

### 4. 测试通知

运行测试脚本：

```bash
python test_feishu.py
```

选择 `2` 测试 API 方式。

---

## 配置文件完整示例

### Webhook 方式（推荐）

```json
{
  "kol_username": "goingsun",
  "scheduler_config": {
    "enabled": true,
    "interval_hours": 1,
    "interval_minutes": 0,
    "headless": true,
    "run_immediately": false
  },
  "database": {
    "db_path": "database/binance_square.db"
  },
  "feishu": {
    "enabled": true,
    "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxxx"
  }
}
```

### API 方式

```json
{
  "kol_username": "goingsun",
  "scheduler_config": {
    "enabled": true,
    "interval_hours": 1,
    "interval_minutes": 0,
    "headless": true,
    "run_immediately": false
  },
  "database": {
    "db_path": "database/binance_square.db"
  },
  "feishu": {
    "enabled": true,
    "app_id": "cli_xxxxxxxxxxxxxxxx",
    "app_secret": "xxxxxxxxxxxxxxxxxxxxxxxx",
    "receive_id": "oc_xxxxxxxxxxxxxxxx",
    "receive_id_type": "chat_id"
  }
}
```

---

## 消息格式

### 文本消息

简单的纯文本消息。

### 富文本消息（默认）

当发现新文章时，会发送富文本格式的消息，包含：

- 文章数量
- 每篇文章的标题、内容摘要、发布时间
- 文章链接（跳转到 KOL 主页）

**示例消息：**

```
🔔 币安广场新文章通知 - goingsun

发现 2 篇新文章

📄 文章 1
标题: BTC 分析报告
内容: 比特币近期走势分析...
时间: 2024-01-01 10:00:00
[查看原文]

📄 文章 2
标题: ETH 市场动态
内容: 以太坊价格变动...
时间: 2024-01-01 11:00:00
[查看原文]
```

---

## 常见问题

### Q1: Webhook 方式发送失败？

A: 检查以下几点：
1. Webhook URL 是否正确
2. 机器人是否被移除出群
3. 是否配置了签名验证（当前版本暂不支持）

### Q2: API 方式提示权限不足？

A: 确保应用已添加必要权限并发布版本。

### Q3: 如何只在有新文章时才发送通知？

A: 项目默认行为就是只在有新文章时发送通知，如果数据库中已存在该文章，不会重复通知。

### Q4: 如何自定义消息格式？

A: 修改 `utils/feishu_notifier.py` 中的 `notify_new_articles()` 方法。

### Q5: 是否支持发送图片？

A: 当前版本支持在消息中显示文章的图片链接，但不会直接发送图片。如需发送图片，可以使用飞书的富文本消息格式中的图片标签。

---

## 日志查看

飞书通知的日志记录在 `logs/feishu_notifier.log` 文件中。

如果遇到问题，查看日志可以帮助诊断原因：

```bash
# 查看最新日志
tail -f logs/feishu_notifier.log

# Windows
type logs\feishu_notifier.log
```

---

## 代码集成示例

如果你想在自己的代码中使用飞书通知功能：

```python
from utils.feishu_notifier import FeishuNotifier
from scrapers import BinanceSquareScraper

# 创建飞书通知器
notifier = FeishuNotifier(
    webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
    enabled=True
)

# 创建爬虫并传入通知器
scraper = BinanceSquareScraper(
    kol_username="goingsun",
    save_to_db=True,
    feishu_notifier=notifier
)

# 执行爬取（会自动发送通知）
with scraper:
    new_articles = scraper.scrape()
```

---

## 禁用飞书通知

如果不需要飞书通知，在 `config.json` 中设置：

```json
{
  "feishu": {
    "enabled": false
  }
}
```

或者完全删除 `feishu` 配置项。

---

## 技术细节

- 使用飞书开放平台的消息发送 API
- 支持文本消息和富文本消息（post）
- 自动获取和刷新 access_token
- 完整的错误处理和日志记录
- 支持超时设置（默认 10 秒）
