from datetime import datetime

from scripts.models import Race
from scripts.providers.nar_provider import NARProvider


class LocalFetcher:

    def __init__(self) -> None:
        self.provider = NARProvider()

    def get_today_races(self):

        print("地方競馬開催情報取得")

        # 接続確認
        html = self.provider.fetch_top_page()

        print(f"NAR HTML取得成功（{len(html)}文字）")

        races = []

        # まだ解析はしない
        races.append(
            Race(
                race_date=datetime.today().strftime("%Y-%m-%d"),
                organization="地方",
                place="大井",
                race_no=11,
                race_name="サンプル",
                distance=1600,
                track="ダート",
                weather="晴"
            )
        )

        return races