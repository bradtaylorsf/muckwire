---
name: opencorporates
description: "OpenCorporates global company registry lookup; requires OPENCORPORATES_API_KEY and is useful for company numbers, jurisdictions, officers, filings, and registered agents."
when_to_use: "global company registry lookup, shell-company tracing, jurisdiction/company number lookup, officer and registered-agent facts"
when_not_to_use: "SEC-reporting public-company disclosures -> edgar; US state business portal deep pages -> sos; nonprofit Form 990s -> nonprofits"
---

# OpenCorporates connector

`opencorporates_search` queries the OpenCorporates v0.4 company search API and `opencorporates_fetch` resolves a company permalink into a profile summary.

## Payload

- `query` - company or officer/agent name.
- `sub_question` - what the downstream extraction should answer.
- `jurisdiction` - optional OpenCorporates jurisdiction code, such as `us_ca`, `us_de`, or `gb`.
- `max_results` - default 20.

Example:

```yaml
kind: opencorporates_search
payload:
  query: "Acme Holdings"
  sub_question: "Which registered entities and jurisdictions match Acme Holdings?"
  jurisdiction: us_ca
  max_results: 10
```

## Auth, cost, and freshness

- `OPENCORPORATES_API_KEY` is required for live API calls.
- Anonymous v0.4 access is no longer reliable; the connector skips search/fetch without a key rather than making a guaranteed 401 request.
- Public-benefit access may be free after approval; commercial access can be expensive. Do not use this connector for broad exploratory sweeps when Secretary of State or EDGAR sources cover the question.
- OpenCorporates mirrors upstream registries, so freshness depends on the underlying jurisdiction and OpenCorporates ingestion.

## Query guidance

- Add `jurisdiction` when the state/country is known. It improves precision and reduces paid/API usage.
- Use company names for search. Use `fetch()` on exact `/companies/<jurisdiction>/<company_number>` URLs for officers, filings, registered agent, and associated entities.
- Treat registry presence as evidence of an entity filing, not proof of current operations.

## Failure modes

- Missing `OPENCORPORATES_API_KEY` returns no results and logs a skip.
- Jurisdiction codes vary by country and state. Bad codes usually produce empty results.
- Some jurisdictions hide officer or registered-agent details; cite the available fields and replan to the official state registry when details are missing.
