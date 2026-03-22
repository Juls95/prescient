-- Prescient: Recent Protocol Deployments on Base
-- Finds new contract deployments in the last 7 days.
-- Expected columns: contract_address, deployer, contract_name, block_time, tx_hash

SELECT
    address AS contract_address,
    "from" AS deployer,
    COALESCE(namespace, SUBSTRING(CAST(address AS VARCHAR), 1, 10)) AS contract_name,
    block_time,
    creation_tx_hash AS tx_hash
FROM base.creation_traces
WHERE block_time > NOW() - INTERVAL '7' DAY
ORDER BY block_time DESC
LIMIT 50
