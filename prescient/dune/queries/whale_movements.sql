-- Prescient: Whale Movements on Base
-- Finds large-value transfers in the last 24 hours.
-- Expected columns: token_symbol, value_usd, from_address, to_address, tx_hash, chain
-- Parameter: {{min_value}} (default 500000)

SELECT
    t.symbol AS token_symbol,
    (tr.value / POW(10, t.decimals)) * p.price AS value_usd,
    tr."from" AS from_address,
    tr."to" AS to_address,
    tr.tx_hash,
    'base' AS chain
FROM base.erc20_transfers tr
JOIN tokens.erc20 t
    ON tr.contract_address = t.contract_address
    AND t.blockchain = 'base'
JOIN prices.usd p
    ON p.contract_address = t.contract_address
    AND p.blockchain = 'base'
    AND p.minute = DATE_TRUNC('hour', tr.block_time)
WHERE tr.block_time > NOW() - INTERVAL '24' HOUR
  AND (tr.value / POW(10, t.decimals)) * p.price >= {{min_value}}
ORDER BY value_usd DESC
LIMIT 50
