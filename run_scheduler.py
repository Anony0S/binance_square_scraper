"""
定时爬虫启动脚本
快速启动定时调度器
"""

import sys
from utils.scheduler import SchedulerManager


def main():
    """主函数"""
    print("=" * 80)
    print("币安广场定时爬虫")
    print("=" * 80)
    print()

    try:
        # 创建调度管理器
        manager = SchedulerManager(config_path="config.json")

        # 设置任务
        manager.setup_jobs()

        # 启动调度器
        manager.start()

    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
