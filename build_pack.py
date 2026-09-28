"""June operating-profit bridge for a fictional Bratislava wholesaler.

Volume, price, and unit cost are computed in SQL. They have to add up
to the gap between budget profit and actual profit, including overhead.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "profit.db"
REPORT_PATH = ROOT / "pack" / "index.html"
SCHEMA = (ROOT / "schema.sql").read_text(encoding="utf-8")


def euro(amount: int) -> str:
    sign = "−" if amount < 0 else ""
    return f"{sign}€{abs(amount):,}"


def build() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO products (sku, name) VALUES (?, ?)",
        [("VALVE", "Valve"), ("HOSE", "Hose"), ("FITTING", "Fitting")],
    )
    conn.executemany(
        "INSERT INTO budget (sku, qty, price_eur, unit_cost_eur) VALUES (?, ?, ?, ?)",
        [
            ("VALVE", 1000, 80, 50),
            ("HOSE", 2000, 40, 28),
            ("FITTING", 500, 20, 16),
        ],
    )
    conn.executemany(
        "INSERT INTO actual (sku, qty, price_eur, unit_cost_eur) VALUES (?, ?, ?, ?)",
        [
            ("VALVE", 800, 74, 52),
            ("HOSE", 2100, 40, 30),
            ("FITTING", 1400, 19, 16),
        ],
    )
    conn.executemany(
        "INSERT INTO overhead (name, budget_eur, actual_eur) VALUES (?, ?, ?)",
        [
            ("Warehouse and admin", 40000, 41500),
            ("One-off advisory", 0, 3000),
        ],
    )
    conn.commit()
    return conn


def query(conn: sqlite3.Connection, name: str) -> list[sqlite3.Row]:
    sql = (ROOT / "sql" / name).read_text(encoding="utf-8")
    return list(conn.execute(sql))


def waterfall(steps: list[tuple[str, int, str]]) -> str:
    values = [step[1] for step in steps]
    low = min(0, *values)
    high = max(0, *values)
    span = high - low or 1
    width = 760
    height = 280
    left = 36
    top = 24
    plot_h = 210
    slot = (width - left - 16) / len(steps)
    bar_w = 48

    def y(value: int) -> float:
        return top + (high - value) / span * plot_h

    zero = y(0)
    parts = [
        f'<line x1="{left}" y1="{zero:.1f}" x2="{width - 8}" y2="{zero:.1f}" stroke="#bbb"/>'
    ]
    cursor = 0
    for index, (label, delta, kind) in enumerate(steps):
        x = left + index * slot + (slot - bar_w) / 2
        if kind == "total":
            start, end = 0, delta
            if index == 0:
                cursor = delta
        else:
            start, end = cursor, cursor + delta
            cursor = end
        y0, y1 = y(start), y(end)
        top_y = min(y0, y1)
        bar_h = max(abs(y1 - y0), 1)
        fill = "#161616" if kind == "total" else ("#9f1d1d" if delta < 0 else "#0f6e56")
        parts.append(f'<rect x="{x:.1f}" y="{top_y:.1f}" width="{bar_w}" height="{bar_h:.1f}" fill="{fill}"/>')
        parts.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{height - 28}" text-anchor="middle" font-size="11" fill="#333">{label}</text>'
        )
        parts.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{top_y - 6:.1f}" text-anchor="middle" font-size="11" fill="#161616">{euro(delta)}</text>'
        )
    return f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Operating profit bridge">{"".join(parts)}</svg>'


def render(conn: sqlite3.Connection) -> None:
    sku_rows = query(conn, "01_sku_bridge.sql")
    bridge = query(conn, "02_profit_bridge.sql")[0]
    if bridge["unexplained_eur"] != 0:
        raise SystemExit(f"bridge does not tie: {bridge['unexplained_eur']}")
    if any(row["sku_unexplained_eur"] != 0 for row in sku_rows):
        raise SystemExit("a product bridge does not tie")

    budget = bridge["budget_profit_eur"]
    actual = bridge["actual_profit_eur"]
    gap = actual - budget
    steps = [
        ("Budget", budget, "total"),
        ("Volume", bridge["volume_eur"], "delta"),
        ("Price", bridge["price_eur"], "delta"),
        ("Cost", bridge["cost_eur"], "delta"),
        ("Overhead", bridge["overhead_eur"], "delta"),
        ("One-off", bridge["one_off_eur"], "delta"),
        ("Actual", actual, "total"),
    ]

    body = []
    for row in sku_rows:
        body.append(
            "<tr>"
            f"<td>{row['name']}</td>"
            f"<td class='num'>{row['budget_qty']:,} → {row['actual_qty']:,}</td>"
            f"<td class='num'>{euro(row['budget_price_eur'])} → {euro(row['actual_price_eur'])}</td>"
            f"<td class='num'>{euro(row['budget_unit_cost_eur'])} → {euro(row['actual_unit_cost_eur'])}</td>"
            f"<td class='num'>{euro(row['volume_eur'])}</td>"
            f"<td class='num'>{euro(row['price_eur'])}</td>"
            f"<td class='num'>{euro(row['cost_eur'])}</td>"
            "</tr>"
        )

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>June profit bridge · North Wharf</title>
  <style>
    body {{ margin: 0; background: #fff; color: #161616; font-family: "Segoe UI", sans-serif; }}
    main {{ width: min(920px, calc(100% - 32px)); margin: 0 auto; padding: 32px 0 56px; }}
    .kicker {{ font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; margin: 0; }}
    h1 {{ font-size: 34px; font-weight: 600; letter-spacing: -0.03em; margin: 8px 0; }}
    p {{ line-height: 1.45; max-width: 68ch; }}
    svg {{ width: 100%; height: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ text-align: left; padding: 8px 6px; border-bottom: 1px solid #e4e4e4; }}
    th {{ font-size: 11px; letter-spacing: 0.04em; text-transform: uppercase; color: #555; }}
    .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
    footer {{ margin-top: 24px; color: #555; font-size: 13px; }}
  </style>
</head>
<body>
<main>
  <p class="kicker">North Wharf s.r.o. · Bratislava · June 2026 · fictional</p>
  <h1>Operating profit missed budget by {euro(gap)}.</h1>
  <p>Budget was {euro(budget)}. Actual was {euro(actual)}. Volume is not the story. The miss is the discount on valves, the higher unit cost, and a one-off advisory fee. Extra fittings added little, because that product is the low-margin one.</p>
  {waterfall(steps)}
  <h2>By product</h2>
  <table>
    <thead>
      <tr>
        <th>Product</th><th>Qty</th><th>Price</th><th>Unit cost</th>
        <th>Volume</th><th>Price effect</th><th>Cost effect</th>
      </tr>
    </thead>
    <tbody>
      {''.join(body)}
    </tbody>
  </table>
  <footer>
    Volume uses the budget margin, so selling more fittings does not look like a price change.
    Price and cost use actual quantity. Overhead is warehouse and admin against its own budget.
    The one-off had no budget. The seven bars are the query in sql/02_profit_bridge.sql, and the unexplained column of that query is zero.
  </footer>
</main>
</body>
</html>
"""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(page, encoding="utf-8")
    print(
        f"budget={budget} actual={actual} gap={gap} "
        f"volume={bridge['volume_eur']} price={bridge['price_eur']} "
        f"cost={bridge['cost_eur']} overhead={bridge['overhead_eur']} one_off={bridge['one_off_eur']}"
    )
    print(REPORT_PATH)


if __name__ == "__main__":
    connection = build()
    try:
        render(connection)
    finally:
        connection.close()
