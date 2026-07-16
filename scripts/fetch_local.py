from scripts.models import Race
from scripts.parsers.nar_parser import NARParser
from scripts.providers.nar_provider import NARProvider


class LocalFetcher:
    """
    地方競馬レース取得
    """

    def __init__(self) -> None:
        self.provider = NARProvider()
        self.parser = NARParser()

    def get_today_races(
        self,
    ) -> list[Race]:
        """
        今日の地方競馬レース一覧を取得する。
        """

        print(
            "地方競馬開催情報取得"
        )

        # 開催一覧HTML取得
        html = (
            self.provider
            .fetch_today_race_list()
        )

        # 開催一覧解析
        meetings = (
            self.parser
            .parse_today_race_list(
                html
            )
        )

        print(
            "===== 今日の開催 ====="
        )

        all_races: list[Race] = []

        for meeting in meetings:

            print(
                f"{meeting.place} : "
                f"{meeting.race_list_url}"
            )

            print(
                f"DEBUG DATE: "
                f"{meeting.place} "
                f"{meeting.race_date}"
            )

            # 開催別RaceList取得
            race_html = (
                self.provider
                .fetch_race_list(
                    meeting.race_list_url
                )
            )

            # Race解析
            races = (
                self.parser
                .parse_race_list(
                    race_html,
                    meeting,
                )
            )

            all_races.extend(
                races
            )

        return all_races