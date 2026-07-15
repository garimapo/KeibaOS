from scripts.models import Race


class LocalFetcher:

    def get_today_races(self):

        print("地方競馬開催情報取得")

        races = []

        races.append(
            Race(
                race_date="2026-07-15",
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