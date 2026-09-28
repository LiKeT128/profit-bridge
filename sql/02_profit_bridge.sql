-- Budget operating profit to actual. Unexplained must be zero.
-- Overhead and the one-off sit below contribution, so they reduce profit when they rise.

WITH sku AS (
  SELECT
    SUM(budget_contribution_eur) AS budget_contribution_eur,
    SUM(actual_contribution_eur) AS actual_contribution_eur,
    SUM(volume_eur) AS volume_eur,
    SUM(price_eur) AS price_eur,
    SUM(cost_eur) AS cost_eur
  FROM v_sku_bridge
),
oh AS (
  SELECT
    SUM(budget_eur) AS budget_eur,
    SUM(CASE WHEN name = 'One-off advisory' THEN 0 ELSE actual_eur END) AS run_rate_actual_eur,
    SUM(CASE WHEN name = 'One-off advisory' THEN actual_eur ELSE 0 END) AS one_off_eur
  FROM overhead
)
SELECT
  sku.budget_contribution_eur - oh.budget_eur AS budget_profit_eur,
  sku.volume_eur,
  sku.price_eur,
  sku.cost_eur,
  -(oh.run_rate_actual_eur - oh.budget_eur) AS overhead_eur,
  -oh.one_off_eur AS one_off_eur,
  sku.actual_contribution_eur - oh.run_rate_actual_eur - oh.one_off_eur AS actual_profit_eur,
  (sku.budget_contribution_eur - oh.budget_eur)
    + sku.volume_eur + sku.price_eur + sku.cost_eur
    - (oh.run_rate_actual_eur - oh.budget_eur)
    - oh.one_off_eur
    - (sku.actual_contribution_eur - oh.run_rate_actual_eur - oh.one_off_eur) AS unexplained_eur
FROM sku, oh;
