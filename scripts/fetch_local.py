from scripts.models import Race
from scripts.database import save_race, get_race_id, save_horse
from scripts.parsers.nar_parser import NARParser
from scripts.parsers.horse_parser import HorseParser
from scripts.providers.nar_provider import NARProvider


class LocalFetcher:
    """
    地方競馬レース取得
    """

    def __init__(self) -> None:

        self.provider = NARProvider()
        self.parser = NARParser()
        self.horse_parser = HorseParser()


    def get_today_races(
        self,
    ) -> list[Race]:
        """
        今日の地方競馬レース一覧を取得する。
        """

        print(
            "地方競馬開催情報取得"
        )


        html = (
            self.provider
            .fetch_today_race_list()
        )


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


            race_html = (
                self.provider
                .fetch_race_list(
                    meeting.race_list_url
                )
            )


            races = (
                self.parser
                .parse_race_list(
                    race_html,
                    meeting,
                )
            )


            print(
                f"{meeting.place} "
                f"Race数: {len(races)}"
            )


            for race in races:

                if not race.deba_table_url:

                    continue


                print(
                    f"出馬表取得: "
                    f"{race.place} "
                    f"{race.race_no}R"
                )


                # Race ID取得
                race_id = get_race_id(
                    race
                )


                # 未登録なら保存
                if race_id is None:

                    race_id = save_race(
                        race
                    )


                if race_id is None:

                    print(
                        f"{race.place} "
                        f"{race.race_no}R "
                        "Race ID取得失敗"
                    )

                    continue


                # 出馬表HTML取得
                deba_html = (
                    self.provider
                    .fetch_deba_table(
                        race.deba_table_url
                    )
                )


                # Horse解析
                horses = (
                    self.horse_parser
                    .parse(
                        deba_html,
                        race_id,
                    )
                )


                saved_count = 0


                for horse in horses:

                    if save_horse(
                        horse
                    ):

                        saved_count += 1


                print(
                    f"{race.place} "
                    f"{race.race_no}R "
                    f"馬取得: {len(horses)}頭 "
                    f"保存: {saved_count}頭"
                )


            all_races.extend(
                races
            )


        return all_races