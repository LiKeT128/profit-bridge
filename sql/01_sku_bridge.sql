-- One row per product. Volume, price, and cost must sum to the contribution gap.
SELECT
  name,
  budget_qty,
  actual_qty,
  budget_price_eur,
  actual_price_eur,
  budget_unit_cost_eur,
  actual_unit_cost_eur,
  budget_contribution_eur,
  actual_contribution_eur,
  volume_eur,
  price_eur,
  cost_eur,
  volume_eur + price_eur + cost_eur
    - (actual_contribution_eur - budget_contribution_eur) AS sku_unexplained_eur
FROM v_sku_bridge
ORDER BY name;
