# MEOK MCP Test MCP

> **Drop-in golden-file + schema-drift + tool-failure test harness for ANY MCP server.** Generates a pytest template, produces an HMAC-signed test report, prints a Shields.io grade badge for your README.

> 🧪 **Part of the MEOK Governance Substrate (£499/mo)** — combine with `mcp-spec-compliance-mcp` (spec audit) + `meok-mcp-hardening-mcp` (security red-team) for the full pre-publish gate.

## Why this exists

Thousands of MCPs ship zero tests. MCP Inspector is debug-only. Anthropic Registry will probably enforce some baseline by Q4 2026. Every MCP author wants a green check **before** submitting.

This MCP gives you:

| Test | What it catches |
|---|---|
| `validate_server_json` | Missing name/version/description/repo |
| `validate_tool_schema` | Tool name not alphanumeric, description <5 or >1024 chars, invalid JSON Schema type |
| `diff_server_json` | Breaking changes (removed keys, type flips) |
| `run_golden_diff` | Snapshot drift |
| `check_idempotency_static` | Non-deterministic read-only tools |
| `generate_test_template` | Pytest scaffolding so authors can drop tests in CI |
| `run_test_suite` | The full default flow above as one call |
| `sign_test_report` | HMAC seal + Shields.io badge URL |

## Quick start

```bash
pip install meok-mcp-test-mcp
# or
uvx meok-mcp-test-mcp
```

```python
from server import run_test_suite, sign_test_report

report = run_test_suite(
    server_json=my_server_json,
    golden_pairs=[
        {"name": "list_chains", "actual": actual_out, "expected": expected_out},
    ],
    schema_drift_baseline=last_known_good_server_json,
)
sealed = sign_test_report(report)
print(sealed["badge_url"])  # paste in your README
```

## Tools exposed

- `run_test_suite(server_json, golden_pairs?, schema_drift_baseline?)` — full default suite
- `validate_server_json(server_json)` — structural validation
- `validate_tool_schema(tool)` — single tool deep-check
- `diff_server_json(old, new)` — structural diff with breaking-change flag
- `run_golden_diff(actual, expected)` — single snapshot check
- `check_idempotency_static(samples)` — given N samples, return whether all equal
- `generate_test_template()` — pytest scaffolding
- `sign_test_report(report)` — HMAC-seal + Shields.io badge

## Wire it up to your CI

```yaml
# .github/workflows/mcp-test.yml
name: MEOK MCP Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install meok-mcp-test-mcp
      - run: python -m server  # runs the included pytest scaffold
```

## Scoring

- A ≥ 90% passed
- B ≥ 75%
- C ≥ 60%
- D ≥ 40%
- F otherwise

## Verify any signed report

Paste any signed test report at https://meok.ai/verify — the HMAC signature is checked against MEOK's public JWKS.

## Pricing

- Self-host: free (MIT)
- Starter: £29/mo — 1K test runs/mo + signed badge SLA
- Pro: £79/mo — 10K runs/mo + custom badge + public dashboard
- Governance Substrate: £499/mo — bundled with 10 governance MCPs
- A2A Substrate: £999/mo — bundled with all 12 A2A MCPs

## Companion MCPs

- `mcp-spec-compliance-mcp` — registry-spec conformity audit
- `meok-mcp-hardening-mcp` — OWASP LLM Top 10 + 5 MCP-specific risks
- `meok-mcp-cardgen-mcp` — generate `.well-known/mcp` cards
- `meok-agents-md-lint-mcp` — AGENTS.md spec lint

## Legal

Built by [MEOK AI Labs](https://meok.ai) — trading name of CSOAI LTD, UK Companies House 16939677.
Founder: Nicholas Templeman (`nicholas@meok.ai`).
License: MIT.
