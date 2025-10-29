"""
数据库操作模块
提供 SQLite 数据库的初始化、增删改查等操作
"""

import hashlib
import json
import sqlite3
from datetime import datetime
from typing import Any, Optional

from utils.logger import setup_logger

logger = setup_logger(
    logger_name="database",
    log_file="database.log",
    log_level=20,  # logging.INFO
)


class DatabaseManager:
    """数据库管理类，封装所有数据库操作"""

    def __init__(self, db_path: str = "binance_square.db"):
        """
        初始化数据库管理器

        :param db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None

    def connect(self):
        """连接到数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
            self.cursor = self.conn.cursor()
            logger.info(f"✓ 成功连接到数据库: {self.db_path}")
        except Exception as e:
            logger.error(f"× 连接数据库失败: {str(e)}")
            raise

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("✓ 数据库连接已关闭")

    def init_table(self):
        """初始化数据库表"""
        try:
            # 创建文章表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_hash TEXT UNIQUE NOT NULL,
                    author TEXT NOT NULL,
                    card_title TEXT,
                    card_description TEXT NOT NULL,
                    create_time TEXT,
                    imgs TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建索引以提高查询性能
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_hash
                ON articles(content_hash)
            """)

            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_author
                ON articles(author)
            """)

            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_create_time
                ON articles(create_time)
            """)

            self.conn.commit()
            logger.info("✓ 数据库表初始化成功")

        except Exception as e:
            logger.error(f"× 初始化数据库表失败: {str(e)}")
            raise

    @staticmethod
    def generate_content_hash(article: dict) -> str:
        """
        生成文章内容的唯一哈希值
        使用 author + card_description 作为唯一标识

        :param article: 文章字典
        :return: SHA256 哈希值
        """
        # 组合多个字段来生成唯一标识
        unique_string = (
            f"{article.get('author', '')}"
            f"{article.get('card_description', '')}"
        )
        return hashlib.sha256(unique_string.encode("utf-8")).hexdigest()

    def insert_article(self, article: dict) -> bool:
        """
        插入单篇文章到数据库

        :param article: 文章字典
        :return: 是否插入成功
        """
        try:
            # 生成内容哈希
            content_hash = self.generate_content_hash(article)

            # 将图片列表转换为 JSON 字符串
            imgs_json = json.dumps(article.get("imgs", []), ensure_ascii=False)

            # 插入数据
            self.cursor.execute(
                """
                INSERT INTO articles
                (content_hash, author, card_title, card_description, create_time, imgs)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    content_hash,
                    article.get("author", ""),
                    article.get("card_title", ""),
                    article.get("card_description", ""),
                    article.get("create-time", ""),
                    imgs_json,
                ),
            )

            self.conn.commit()
            logger.info(f"✓ 成功插入文章: {content_hash[:16]}...")
            return True

        except sqlite3.IntegrityError:
            logger.warning(f"! 文章已存在，跳过插入: {content_hash[:16]}...")
            return False

        except Exception as e:
            logger.error(f"× 插入文章失败: {str(e)}")
            return False

    def insert_articles_batch(self, articles: list[dict]) -> tuple[int, int]:
        """
        批量插入文章

        :param articles: 文章列表
        :return: (成功插入数量, 跳过数量)
        """
        inserted_count = 0
        skipped_count = 0

        logger.info(f"\n{'='*60}")
        logger.info(f"开始批量插入 {len(articles)} 篇文章")
        logger.info(f"{'='*60}")

        for idx, article in enumerate(articles, 1):
            if self.insert_article(article):
                inserted_count += 1
            else:
                skipped_count += 1

            if idx % 10 == 0:
                logger.info(f"进度: {idx}/{len(articles)}")

        logger.info(f"\n{'='*60}")
        logger.info(f"批量插入完成")
        logger.info(f"成功插入: {inserted_count} 篇")
        logger.info(f"跳过重复: {skipped_count} 篇")
        logger.info(f"{'='*60}\n")

        return inserted_count, skipped_count

    def get_article_by_hash(self, content_hash: str) -> Optional[dict]:
        """
        根据内容哈希获取文章

        :param content_hash: 内容哈希值
        :return: 文章字典或 None
        """
        try:
            self.cursor.execute(
                """
                SELECT * FROM articles WHERE content_hash = ?
                """,
                (content_hash,),
            )

            row = self.cursor.fetchone()
            if row:
                return dict(row)
            return None

        except Exception as e:
            logger.error(f"× 查询文章失败: {str(e)}")
            return None

    def get_articles_by_author(self, author: str) -> list[dict]:
        """
        根据作者获取所有文章

        :param author: 作者用户名
        :return: 文章列表
        """
        try:
            self.cursor.execute(
                """
                SELECT * FROM articles WHERE author = ?
                ORDER BY create_time DESC
                """,
                (author,),
            )

            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"× 查询文章失败: {str(e)}")
            return []

    def get_all_articles(self, limit: int = 100) -> list[dict]:
        """
        获取所有文章

        :param limit: 返回数量限制
        :return: 文章列表
        """
        try:
            self.cursor.execute(
                """
                SELECT * FROM articles
                ORDER BY scraped_at DESC
                LIMIT ?
                """,
                (limit,),
            )

            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"× 查询文章失败: {str(e)}")
            return []

    def get_article_count(self) -> int:
        """
        获取文章总数

        :return: 文章数量
        """
        try:
            self.cursor.execute("SELECT COUNT(*) as count FROM articles")
            result = self.cursor.fetchone()
            return result["count"] if result else 0

        except Exception as e:
            logger.error(f"× 查询文章数量失败: {str(e)}")
            return 0

    def delete_article_by_hash(self, content_hash: str) -> bool:
        """
        根据内容哈希删除文章

        :param content_hash: 内容哈希值
        :return: 是否删除成功
        """
        try:
            self.cursor.execute(
                """
                DELETE FROM articles WHERE content_hash = ?
                """,
                (content_hash,),
            )

            self.conn.commit()
            deleted_count = self.cursor.rowcount

            if deleted_count > 0:
                logger.info(f"✓ 成功删除文章: {content_hash[:16]}...")
                return True
            else:
                logger.warning(f"! 文章不存在: {content_hash[:16]}...")
                return False

        except Exception as e:
            logger.error(f"× 删除文章失败: {str(e)}")
            return False

    def update_article(self, content_hash: str, updates: dict) -> bool:
        """
        更新文章信息

        :param content_hash: 内容哈希值
        :param updates: 要更新的字段字典
        :return: 是否更新成功
        """
        try:
            # 构建 UPDATE 语句
            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values())
            values.append(content_hash)

            # 添加更新时间
            set_clause += ", updated_at = CURRENT_TIMESTAMP"

            self.cursor.execute(
                f"""
                UPDATE articles
                SET {set_clause}
                WHERE content_hash = ?
                """,
                values,
            )

            self.conn.commit()
            updated_count = self.cursor.rowcount

            if updated_count > 0:
                logger.info(f"✓ 成功更新文章: {content_hash[:16]}...")
                return True
            else:
                logger.warning(f"! 文章不存在: {content_hash[:16]}...")
                return False

        except Exception as e:
            logger.error(f"× 更新文章失败: {str(e)}")
            return False

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        self.init_table()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
