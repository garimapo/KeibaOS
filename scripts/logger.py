"""
KeibaOS Logger

プロジェクト全体で共通利用するロガーを生成する。
ログは logs/keiba.log に保存し、同時にコンソールへも表示する。
"""

from pathlib import Path
import logging


# ログ保存フォルダ
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "keiba.log"


def get_logger(name: str = "KeibaOS") -> logging.Logger:
    """
    共通ロガーを取得する。

    Args:
        name (str): ロガー名

    Returns:
        logging.Logger
    """

    logger = logging.getLogger(name)

    # 二重登録防止
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    # ファイル出力
    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    # コンソール出力
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger