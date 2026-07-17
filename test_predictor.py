from scripts.database import (
    get_all_races,
    get_horses_by_race,
)

from scripts.prediction.predictor import predict


def main():

    races = get_all_races()

    if not races:

        print("レースがありません。")

        return

    race_id, race = races[0]

    horses = get_horses_by_race(
        race_id
    )

    # ==========================
    # Horse取得確認
    # ==========================

    print()

    print("========== Horse List ==========")

    for horse in horses:

        print(
            f"{horse.frame_no}-{horse.horse_no} "
            f"{horse.horse_name}"
        )

    print()

    # ==========================
    # AI予想
    # ==========================

    scores = predict(
        race,
        horses,
    )

    print(
        f"{race.place} {race.race_no}R"
    )

    print(
        race.race_name
    )

    print("-" * 60)

    for i, score in enumerate(
        scores,
        start=1,
    ):

        print(
            f"{i:>2}. "
            f"{score.horse.horse_name:<20}"
            f" 人気:{score.horse.popularity:<2}"
            f" オッズ:{score.horse.odds:<5}"
            f" Score:{score.total}"
        )


if __name__ == "__main__":
    main()