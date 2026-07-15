from scripts.models import Race
from scripts.parsers.nar_parser import NARParser
from scripts.providers.nar_provider import NARProvider


class LocalFetcher:
    """
    地方競馬開催情報取得
    """

    def __init__(self) -> None:
        self.provider = NARProvider()
        self.parser = NARParser()

    def get_today_races(self) -> list[Race]:
        """
        今日の地方競馬開催情報を取得する。
        """

        print("地方競馬開催情報取得")

        # 開催一覧HTML取得
        html = self.provider.fetch_today_race_list()

        # 開催一覧解析
        meetings = self.parser.parse_today_race_list(html)

        print("===== 今日の開催 =====")

        for meeting in meetings:
            print(
                f"{meeting.place} : {meeting.race_list_url}"
            )

        # Ver0.6ではRace取得はまだ実装しない
        return []