from scripts.database import create_tables
from scripts.fetch_races import fetch_today_races


def main():

    print("[START] KeibaAI")

    create_tables()

    print("[OK] Database Ready")

    fetch_today_races()

    print("[END]")


if __name__ == "__main__":
    main()