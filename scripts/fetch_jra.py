from scripts.models import Race


class JRAFetcher:

    def get_today_races(self):

        print("JRA開催情報取得")

        races = []

        races.append(
            Race(
                race_date="2026-07-15",
                organization="JRA",
                place="函館",
                race_no=11,
                race_name="サンプル",
                distance=1800,
                track="芝",
                weather="晴"
            )
        )

        return races