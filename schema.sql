PRAGMA foreign_keys = ON;

-- One month, three products. Prices and costs are euros per unit.
-- Contribution is qty * (price - unit cost), before overhead.

CREATE TABLE products (
  sku TEXT PRIMARY KEY,
  name TEXT NOT NULL
);

CREATE TABLE budget (
  sku TEXT PRIMARY KEY REFERENCES products(sku),
  qty INTEGER NOT NULL,
  price_eur INTEGER NOT NULL,
  unit_cost_eur INTEGER NOT NULL
);

CREATE TABLE actual (
  sku TEXT PRIMARY KEY REFERENCES products(sku),
  qty INTEGER NOT NULL,
  price_eur INTEGER NOT NULL,
  unit_cost_eur INTEGER NOT NULL
);

CREATE TABLE overhead (
  name TEXT PRIMARY KEY,
  budget_eur INTEGER NOT NULL,
  actual_eur INTEGER NOT NULL
);

-- Volume keeps the budget margin, so a shift into a cheap product
-- does not get disguised as a price cut.
-- Price uses actual quantity. Cost uses actual quantity.
-- The three effects sum to actual contribution minus budget contribution.
CREATE VIEW v_sku_bridge AS
SELECT
  p.sku,
  p.name,
  b.qty AS budget_qty,
  a.qty AS actual_qty,
  b.price_eur AS budget_price_eur,
  a.price_eur AS actual_price_eur,
  b.unit_cost_eur AS budget_unit_cost_eur,
  a.unit_cost_eur AS actual_unit_cost_eur,
  b.qty * (b.price_eur - b.unit_cost_eur) AS budget_contribution_eur,
  a.qty * (a.price_eur - a.unit_cost_eur) AS actual_contribution_eur,
  (a.qty - b.qty) * (b.price_eur - b.unit_cost_eur) AS volume_eur,
  (a.price_eur - b.price_eur) * a.qty AS price_eur,
  (b.unit_cost_eur - a.unit_cost_eur) * a.qty AS cost_eur
FROM products p
JOIN budget b ON b.sku = p.sku
JOIN actual a ON a.sku = p.sku;
