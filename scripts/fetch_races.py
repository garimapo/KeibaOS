from datetime import datetime

from scripts.database import save_race
from scripts.fetch_jra import JRAFetcher
from scripts.fetch_local import LocalFetcher


def fetch_today_races() -> None:
    """
    当日開催のレースを取得し、SQLiteへ保存する。
    """

    today = datetime.today()

    if today.weekday() >= 5:
        print("JRAモード")
        fetcher = JRAFetcher()
    else:
        print("地方競馬モード")
        fetcher = LocalFetcher()

    races = fetcher.get_today_races()

    print("===== 取得したレース =====")

    saved_count = 0
    skipped_count = 0

    for race in races:
        print(race)

        if save_race(race):
            saved_count += 1
        else:
            skipped_count += 1

    print(f"新規保存 : {saved_count}件")
    print(f"重複スキップ : {skipped_count}件")