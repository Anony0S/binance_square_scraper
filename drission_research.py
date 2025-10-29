"""
币安广场爬虫 - DrissionPage 版本
使用 DrissionPage 爬取币安广场 KOL 文章
"""

import json
from scrapers import BinanceSquareScraper
from utils import setup_logger

# 初始化日志
logger = setup_logger(
    logger_name="drission_research",
    log_file="drission_research.log",
    log_level=20,  # logging.INFO
)


def load_config(config_file: str = "config.json") -> dict:
    """
    加载配置文件

    :param config_file: 配置文件路径
    :return: 配置字典
    """
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        logger.info(f"✓ 成功加载配置文件: {config_file}")
        return config
    except FileNotFoundError:
        logger.error(f"× 配置文件不存在: {config_file}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"× 配置文件格式错误: {str(e)}")
        return {}


def main():
    """主函数 - 执行币安广场文章爬取任务"""
    logger.info("=" * 60)
    logger.info("币安广场 DrissionPage 爬虫")
    logger.info("=" * 60)

    # 1. 加载配置
    config = load_config()
    if not config:
        logger.error("× 无法加载配置，程序退出")
        return

    # 2. 解析配置参数
    kol_username = config.get("kol_username", "BinanceSquareCN")
    drission_config = config.get("drission_config", {})

    headless = drission_config.get("headless", True)
    scroll_times = drission_config.get("scroll_times", 3)
    selectors = drission_config.get("selectors", {})

    logger.info(f"\n配置信息:")
    logger.info(f"  KOL用户名: {kol_username}")
    logger.info(f"  无头模式: {headless}")
    logger.info(f"  滚动次数: {scroll_times}")

    # 3. 执行爬取任务 - 使用上下文管理器自动管理浏览器生命周期
    try:
        with BinanceSquareScraper(
                kol_username=kol_username,
                headless=headless,
                selectors=selectors,
        ) as scraper:
            # 执行爬取
            articles = scraper.scrape()

            # 4. 输出结果
            logger.info(f"\n{'=' * 60}")
            logger.info("提取完成")
            logger.info(f"{'=' * 60}")
            logger.info(f"✓ 共提取 {len(articles)} 篇文章")

            return articles

    except KeyboardInterrupt:
        logger.warning("\n× 用户中断操作")
    except Exception as e:
        logger.error(f"× 发生错误: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
