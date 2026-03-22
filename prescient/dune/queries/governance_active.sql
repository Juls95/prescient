-- Prescient: Active Governance Proposals on Base
-- Finds governance proposals currently open for voting.
-- Expected columns: protocol, proposal_id, title, votes_for, votes_against, end_time, chain

SELECT
    namespace AS protocol,
    proposal_id,
    proposal_title AS title,
    votes_for,
    votes_against,
    end_timestamp AS end_time,
    'base' AS chain
FROM governance.proposals
WHERE blockchain = 'base'
  AND status = 'active'
  AND end_timestamp > NOW()
ORDER BY end_timestamp ASC
LIMIT 20
