from scripts.database import get_horses_by_race

horses = get_horses_by_race(1)

print(f"{len(horses)}頭")

for horse in horses:
    print(
        horse.horse_no,
        horse.horse_name,
        horse.jockey,
    )