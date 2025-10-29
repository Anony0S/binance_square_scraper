"""
币安广场爬虫
专门用于爬取币安广场 KOL 的文章
"""

import time
from time import sleep
from typing import Optional

from scrapers import BaseScraper
from utils.logger import setup_logger
from utils.database import DatabaseManager

logger = setup_logger(
    logger_name="binance_square_scraper",
    log_file="binance_square_scraper.log",
    log_level=20,  # logging.INFO
)


class BinanceSquareScraper(BaseScraper):
    """币安广场爬虫类，继承自 BaseScraper"""

    def __init__(
        self,
        kol_username: str,
        headless: bool = False,
        selectors: dict = None,
        db_path: str = "database/binance_square.db",
        save_to_db: bool = True,
        feishu_notifier=None,
    ):
        """
        初始化币安广场爬虫

        :param kol_username: KOL的用户名
        :param headless: 是否使用无头模式
        :param selectors: 自定义选择器字典
        :param db_path: 数据库文件路径
        :param save_to_db: 是否保存到数据库
        :param feishu_notifier: 飞书通知器实例
        """
        super().__init__(headless=headless)

        self.kol_username = kol_username
        self.profile_url = (
            f"https://www.binance.com/zh-CN/square/profile/{kol_username}"
        )
        self.save_to_db = save_to_db
        self.db_path = db_path
        self.db_manager = None  # 数据库管理器实例
        self.feishu_notifier = feishu_notifier  # 飞书通知器

        # 默认选择器
        self.selectors = selectors or {
            "title": '[class*="title"]',
            "content": '[class*="content"]',
            "time": '[class*="time"]',
        }

    def navigate_to_profile(self) -> bool:
        """
        导航到KOL主页

        :return: 是否成功
        """
        logger.info(f"\n{'=' * 60}")
        logger.info(f"访问KOL主页: {self.profile_url}")
        logger.info(f"{'=' * 60}")

        try:
            self.page.set.window.max()
            self.page.get(self.profile_url)
            logger.info("✓ 页面加载成功")

            # 检查是否有Cloudflare验证
            page_text = self.page.html
            if (
                "cloudflare" in page_text.lower()
                or "checking your browser" in page_text.lower()
            ):
                logger.warning("! 检测到Cloudflare验证，等待验证通过...")
                time.sleep(5)

            # 接受所有 Cookie
            cookie_ele = self.page.ele("text:接受所有 Cookie", timeout=0)
            if cookie_ele and cookie_ele.states.is_in_viewport:
                cookie_ele.click()

            # 提示跳转
            confirm_ele = self.page.ele("@class=bn-modal-confirm", timeout=1)
            try:
                confirm_ele.ele("tag=button").click()
            except Exception as e:
                logger.error(f"未点击到弹窗: {str(e)}")
            return True

        except Exception as e:
            logger.error(f"× 页面加载失败: {str(e)}")
            return False

    def _parse_article_element(self, article_elem) -> dict | None:
        """
        解析单个文章元素

        :param article_elem: 文章元素
        :return: 文章字典或 None（如果解析失败）
        """
        try:
            # 过滤置顶消息
            if article_elem.ele(".:text-EmphasizeText", timeout=0):
                logger.info("跳过置顶文章")
                return None

            # 滚动到元素可见
            self.page.scroll.to_see(article_elem)
            has_img = article_elem.ele(
                "@class:card-images-box", timeout=1
            ).wait.displayed(timeout=1, raise_err=False)

            # 提取文章信息
            article = {
                "author": article_elem.ele("@class=nick-username", timeout=0)
                .child()
                .text,
                "card_title": (
                    article_elem.ele("@class:card__title", timeout=0).child().text
                    if article_elem.ele("@class:card__title", timeout=0)
                    else ""
                ),
                "card_description": article_elem.ele(
                    "@class:card__description", timeout=0
                ).text,
                "create-time": article_elem.ele("@class=create-time", timeout=0).text,
                "imgs": [
                    img_ele.attr("src")
                    for img_ele in article_elem.ele(
                        "@class:card-images-box", timeout=0
                    ).eles("tag:img")
                    if has_img
                ],
            }

            return article

        except Exception as e:
            logger.error(f"× 解析文章元素失败: {str(e)}")
            return None

    def _is_article_in_db(self, article: dict) -> bool:
        """
        检查文章是否已存在于数据库中

        :param article: 文章字典
        :return: 是否存在
        """
        if not self.db_manager:
            return False

        content_hash = self.db_manager.generate_content_hash(article)
        existing_article = self.db_manager.get_article_by_hash(content_hash)
        return existing_article is not None

    def extract_articles(self) -> list[dict]:
        """
        递归提取文章信息（边滚动边检查数据库）
        当遇到已存在的文章时停止

        :return: 新文章列表
        """
        logger.info(f"\n{'=' * 60}")
        logger.info("开始提取文章（遇到重复则停止）")
        logger.info(f"{'=' * 60}")

        new_articles = []  # 新文章列表
        total_processed = 0  # 已处理的文章数
        consecutive_duplicates = 0  # 连续重复计数
        max_consecutive_duplicates = 2  # 连续重复次数阈值

        try:
            # 初始化数据库管理器（如果启用）
            if self.save_to_db and not self.db_manager:
                self.db_manager = DatabaseManager(self.db_path)
                self.db_manager.connect()
                self.db_manager.init_table()

            # 获取当前页面的所有文章元素
            try:
                article_elements = self.page.ele(".:FeedList", timeout=2).children()

                # 处理新加载的文章
                for idx in range(total_processed, len(article_elements)):
                    article_elem = article_elements[-idx]

                    # 解析文章
                    article = self._parse_article_element(article_elem)

                    if article is None:
                        # 置顶文章，跳过
                        total_processed += 1
                        continue

                    # 检查是否已存在于数据库
                    if self._is_article_in_db(article):
                        consecutive_duplicates += 1
                        logger.warning(
                            f"! 发现重复文章 [{consecutive_duplicates}/{max_consecutive_duplicates}]: "
                            f"{article.get('card_title', '无标题')[:30]}..."
                        )

                        # 如果连续遇到多个重复，停止爬取
                        if consecutive_duplicates >= max_consecutive_duplicates:
                            logger.info(
                                f"\n{'=' * 60}\n"
                                f"连续遇到 {consecutive_duplicates} 篇重复文章，停止爬取\n"
                                f"{'=' * 60}"
                            )
                            total_processed += 1
                            # 关闭数据库连接
                            if self.db_manager:
                                self.db_manager.close()
                                self.db_manager = None
                            return new_articles

                        total_processed += 1
                        continue

                    # 重置连续重复计数
                    consecutive_duplicates = 0

                    # 新文章，保存到数据库
                    if self.save_to_db and self.db_manager:
                        if self.db_manager.insert_article(article):
                            logger.info(
                                f"✓ 新文章已保存: {article.get('card_title', '无标题')[:30]}..."
                            )
                            new_articles.append(article)
                        else:
                            logger.warning("! 文章插入数据库失败")
                    else:
                        # 不使用数据库时，直接添加
                        new_articles.append(article)
                        logger.info(
                            f"✓ 第 {len(new_articles)} 篇: {article.get('card_title', '无标题')[:30]}..."
                        )

                    # 发送飞书通知
                    if self.feishu_notifier:
                        try:
                            self.feishu_notifier.notify_new_article(article)
                        except Exception as e:
                            logger.error(f"× 发送飞书通知失败: {str(e)}")

                    total_processed += 1

                logger.info(f"\n{'=' * 60}")
                logger.info(f"提取完成 - 共获取 {len(new_articles)} 篇新文章")
                logger.info(f"{'=' * 60}\n")

                # 关闭数据库连接
                if self.db_manager:
                    self.db_manager.close()
                    self.db_manager = None

                return new_articles
            except Exception as e:
                logger.error(f"× 获取文章列表失败: {str(e)}")
                raise e

        except Exception as e:
            logger.error(f"× 提取文章失败: {str(e)}")
            # 确保关闭数据库连接
            if self.db_manager:
                self.db_manager.close()
                self.db_manager = None
            return new_articles

    def scrape(self) -> list[dict]:
        """
        执行完整的爬取流程

        :return: 新文章列表
        """
        if not self.navigate_to_profile():
            logger.error("× 无法访问页面，爬取中止")
            return []

        # 提取文章（递归模式，文章已在提取过程中存入数据库）
        return self.extract_articles()
