# AGORA — Project Context for Claude Code

## What this is
AI government built at the AWS x Rebura hackathon (Munich, Jun 12 2026, ~2h build time left).
WHITEPAPER.md is the product spec. We are judged on: working demo 40%, creativity & business
value 25%, use of AgentCore features (Memory, Gateway, Identity) 20%, code quality 15%.
A live demo in front of judges at 15:00 is the only deliverable that matters.

## Verified environment facts (do NOT "fix" these)
- Region: us-west-2 only. Account is a temporary Workshop Studio sandbox (dies tonight).
- Bedrock model IDs: legislature "us.anthropic.claude-sonnet-4-6" (verified working).
  Court target "us.anthropic.claude-fable-5" is NOT enabled in this sandbox
  (AccessDenied; marketplace agreement blocked by private-marketplace policy —
  verified Jun 12). Court uses a fallback chain, currently resolving to
  "us.anthropic.claude-opus-4-6-v1" (verified working). No date suffixes.
- Use `python3` (no `python` alias). Deps installed user-level: strands-agents,
  strands-agents-tools, boto3, streamlit. AWS creds come from the environment role.
- An IAM role like 'agentcore-agent-role' pre-exists for AgentCore workloads.

## Rules
- Synthetic data only. No real personal/financial data. No public S3 buckets.
- Sequential model calls, ≤13 per petition (rate guidance ~1 RPS).
- Reliability over features: anything in the live demo path must degrade gracefully
  (AgentCore Memory fails → fall back to laws.json, warn, continue).
- Verify empirically before committing: run `python3 -m src.cli "<petition>"` end-to-end,
  test the veto petition, confirm `streamlit run app.py` boots.
- Commit per working stage (conventional commits), push to origin main.
