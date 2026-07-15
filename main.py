"""
KeibaOS Main

KeibaOSのエントリーポイント。
システム初期化と当日レース取得を実行する。
"""

from scripts.database import create_tables
from scripts.fetch_races import fetch_today_races
from scripts.logger import get_logger

logger = get_logger()


def main() -> None:
    """
    KeibaOSを起動する。
    """

    logger.info("========== KeibaOS Start ==========")

    try:
        create_tables()
        logger.info("Database Ready")

        fetch_today_races()

        logger.info("========== KeibaOS End ==========")

    except Exception:
        logger.exception("Unexpected error occurred.")
        raise


if __name__ == "__main__":
    main()