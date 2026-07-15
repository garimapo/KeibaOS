from datetime import datetime

from scripts.database import save_race
from scripts.fetch_jra import JRAFetcher
from scripts.fetch_local import LocalFetcher


def fetch_today_races():
    today = datetime.today()

    if today.weekday() >= 5:
        print("JRAモード")
        fetcher = JRAFetcher()
    else:
        print("地方競馬モード")
        fetcher = LocalFetcher()

    races = fetcher.get_today_races()

    print("===== 取得したレース =====")

    for race in races:
        print(race)
        save_race(race)

    print("SQLiteへ保存しました")