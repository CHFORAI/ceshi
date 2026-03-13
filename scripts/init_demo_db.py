import random
import sqlite3


def main() -> None:
    path = "data.db"
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS orders("
        "id INTEGER PRIMARY KEY, "
        "order_date TEXT, "
        "amount REAL, "
        "region TEXT)"
    )
    n = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    if n == 0:
        regions = ["华东", "华南", "华北", "西南"]
        for m in range(1, 13):
            for _ in range(40):
                day = random.randint(1, 28)
                amt = round(random.uniform(50, 800), 2)
                region = random.choice(regions)
                c.execute(
                    "INSERT INTO orders(order_date,amount,region) VALUES(?,?,?)",
                    (f"2025-{m:02d}-{day:02d}", amt, region),
                )
    conn.commit()
    conn.close()
    print("ready", path)


if __name__ == "__main__":
    main()

