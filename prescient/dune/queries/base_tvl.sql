-- Prescient: Base TVL Changes Discovery
-- Finds protocols on Base with significant TVL changes in the last 24 hours.
-- Expected columns: protocol, tvl_usd, change_pct, chain
-- Parameter: {{threshold}} (default 15.0)

WITH current_tvl AS (
    SELECT
        project AS protocol,
        SUM(tvl) AS tvl_usd,
        'base' AS chain
    FROM dune.dex.tvl
    WHERE blockchain = 'base'
      AND block_date = CURRENT_DATE
    GROUP BY project
),
previous_tvl AS (
    SELECT
        project AS protocol,
        SUM(tvl) AS tvl_usd
    FROM dune.dex.tvl
    WHERE blockchain = 'base'
      AND block_date = CURRENT_DATE - INTERVAL '1' DAY
    GROUP BY project
)
SELECT
    c.protocol,
    c.tvl_usd,
    c.chain,
    ROUND(((c.tvl_usd - p.tvl_usd) / NULLIF(p.tvl_usd, 0)) * 100, 2) AS change_pct
FROM current_tvl c
JOIN previous_tvl p ON c.protocol = p.protocol
WHERE ABS((c.tvl_usd - p.tvl_usd) / NULLIF(p.tvl_usd, 0)) * 100 >= {{threshold}}
ORDER BY ABS(change_pct) DESC
LIMIT 20
