"""
定时调度器模块
使用 APScheduler 实现定时爬虫任务调度
"""

import json
import sys
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from scrapers import BinanceSquareScraper
from utils.logger import setup_logger
from utils.database import DatabaseManager
from utils.feishu_notifier import create_feishu_notifier_from_config

# 设置日志
logger = setup_logger(
    logger_name="scheduler",
    log_file="scheduler.log",
    log_level=20,  # logging.INFO
)


class SchedulerManager:
    """定时调度管理器"""

    def __init__(self, config_path: str = "config.json"):
        """
        初始化调度管理器

        :param config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.scheduler = BlockingScheduler()
        self.job_stats = {
            "total_runs": 0,
            "success_runs": 0,
            "failed_runs": 0,
            "last_run_time": "",
            "last_run_status": "",
        }

        # 注册事件监听器
        self.scheduler.add_listener(
            self._job_success_listener, EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._job_error_listener, EVENT_JOB_ERROR
        )

    def _load_config(self) -> dict:
        """加载配置文件"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"✓ 配置文件加载成功: {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"× 配置文件加载失败: {str(e)}")
            sys.exit(1)

    def _job_success_listener(self, event):
        """任务执行成功监听器"""
        self.job_stats["total_runs"] += 1
        self.job_stats["success_runs"] += 1
        self.job_stats["last_run_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.job_stats["last_run_status"] = "success"
        logger.info(f"✓ 任务执行成功 - 统计: {self.job_stats}")

    def _job_error_listener(self, event):
        """任务执行失败监听器"""
        self.job_stats["total_runs"] += 1
        self.job_stats["failed_runs"] += 1
        self.job_stats["last_run_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.job_stats["last_run_status"] = "failed"
        logger.error(f"× 任务执行失败 - 异常: {event.exception}")
        logger.error(f"统计: {self.job_stats}")

    def scrape_job(self):
        """爬虫任务函数"""
        logger.info(f"\n{'=' * 80}")
        logger.info(f"定时任务开始执行 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'=' * 80}")

        try:
            # 获取配置
            kol_username = self.config.get("kol_username", "goingsun")
            scheduler_config = self.config.get("scheduler_config", {})
            headless = scheduler_config.get("headless", True)
            db_path = self.config.get("database", {}).get("db_path", "database/binance_square.db")

            logger.info(f"KOL 用户名: {kol_username}")
            logger.info(f"无头模式: {headless}")
            logger.info(f"数据库路径: {db_path}")

            # 创建飞书通知器
            feishu_notifier = create_feishu_notifier_from_config(self.config)
            if feishu_notifier:
                logger.info("✓ 飞书通知已启用")

            # 创建爬虫实例
            scraper = BinanceSquareScraper(
                kol_username=kol_username,
                headless=headless,
                save_to_db=True,
                db_path=db_path,
                feishu_notifier=feishu_notifier,
            )

            # 执行爬取
            with scraper:
                new_articles = scraper.scrape()

            # 记录结果
            logger.info(f"\n{'=' * 80}")
            logger.info(f"✓ 任务执行完成 - 本次获取 {len(new_articles)} 篇新文章")
            logger.info(f"{'=' * 80}\n")

            # 可选：显示统计信息
            if len(new_articles) > 0:
                with DatabaseManager(db_path) as db:
                    total_count = db.get_article_count()
                    author_count = len(db.get_articles_by_author(kol_username))
                    logger.info(f"数据库统计 - 总文章数: {total_count}, {kol_username} 的文章: {author_count}")

        except Exception as e:
            logger.error(f"× 爬虫任务执行失败: {str(e)}", exc_info=True)
            raise

    def add_interval_job(self, hours: int = 1, minutes: int = 0):
        """
        添加间隔触发任务

        :param hours: 间隔小时数
        :param minutes: 间隔分钟数
        """
        trigger = IntervalTrigger(hours=hours, minutes=minutes)
        self.scheduler.add_job(
            self.scrape_job,
            trigger=trigger,
            id="scrape_interval_job",
            name="间隔爬虫任务",
            replace_existing=True,
        )
        logger.info(f"✓ 已添加间隔任务: 每 {hours} 小时 {minutes} 分钟执行一次")

    def setup_jobs(self):
        """根据配置文件设置任务"""
        scheduler_config = self.config.get("scheduler_config", {})
        enabled = scheduler_config.get("enabled", True)

        if not enabled:
            logger.warning("! 调度器未启用，请在 config.json 中设置 scheduler_config.enabled = true")
            sys.exit(0)

        # 获取间隔配置
        hours = scheduler_config.get("interval_hours", 1)
        minutes = scheduler_config.get("interval_minutes", 0)

        # 添加间隔任务
        self.add_interval_job(hours=hours, minutes=minutes)

        # 是否立即执行一次
        run_immediately = scheduler_config.get("run_immediately", False)
        if run_immediately:
            logger.info("立即执行一次爬虫任务...")
            try:
                self.scrape_job()
            except Exception as e:
                logger.error(f"× 立即执行任务失败: {str(e)}")

    def start(self):
        """启动调度器"""
        logger.info(f"\n{'=' * 80}")
        logger.info("定时调度器启动")
        logger.info(f"{'=' * 80}")

        # 打印所有已注册的任务
        jobs = self.scheduler.get_jobs()
        logger.info(f"已注册任务数量: {len(jobs)}")
        for job in jobs:
            logger.info(f"  - {job.name} (ID: {job.id})")
            logger.info(f"    触发器: {job.trigger}")
            # APScheduler 4.x 兼容性：使用 scheduler 获取 next_run_time
            try:
                # 尝试从调度器获取任务信息
                job_info = self.scheduler.get_job(job.id)
                if hasattr(job_info, 'next_run_time'):
                    logger.info(f"    下次运行: {job_info.next_run_time}")
            except Exception:
                # 如果获取失败，跳过显示下次运行时间
                pass

        logger.info(f"\n{'=' * 80}")
        logger.info("调度器运行中... (按 Ctrl+C 停止)")
        logger.info(f"{'=' * 80}\n")

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("\n接收到停止信号，正在关闭调度器...")
            self.scheduler.shutdown()
            logger.info("✓ 调度器已停止")
            logger.info(f"运行统计: {self.job_stats}")


def main():
    """主函数"""
    try:
        # 创建调度管理器
        manager = SchedulerManager(config_path="../config.json")

        # 设置任务
        manager.setup_jobs()

        # 启动调度器
        manager.start()

    except Exception as e:
        logger.error(f"× 调度器启动失败: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
