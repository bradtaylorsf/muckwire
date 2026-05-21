---
name: opencorporates
description: "OpenCorporates company registry lookup with API-token-gated live access."
when_to_use: "Company/entity lookup across jurisdictions, officers, filings, registered addresses, and registry identifiers."
when_not_to_use: "Campaign committees, nonprofits, sanctions, securities filings, or state portals already covered by a more authoritative connector."
---

# OpenCorporates connector

Use `opencorporates_search` for corporate registry discovery across many
jurisdictions. It is a registry aggregator; when possible, follow links back
to the original jurisdiction record for final citation.

## Official documentation

- API landing page: https://api.opencorporates.com/
- API reference v0.4.8: https://api.opencorporates.com/documentation/API-Reference
- API FAQ: https://api.opencorporates.com/documentation/FAQs

## Auth and cost

`OPENCORPORATES_API_KEY` is required for live requests. The API reference says
an API key is required and is submitted as a query parameter. Open-data uses
may qualify for free access under the OpenCorporates license; paid plans remove
some share-alike restrictions.

## Required payload fields

- `query` - required common field; use company name or officer/entity name.
- `sub_question` - required common field.

## Knobs available

- `jurisdiction` - optional OpenCorporates jurisdiction code such as `us_ca`
  or `gb`.
- `max_results` - optional client cap.

## Valid payload examples

```yaml
kind: opencorporates_search
payload:
  query: "Acme Holdings"
  sub_question: "Which OpenCorporates company records match Acme Holdings?"
  jurisdiction: "us_ca"
  max_results: 10
```

## Request and pagination pattern

Start with company search and add `jurisdiction` when the target state/country
is known. Company detail pages may expose company number, jurisdiction code,
current status, officers, registered address, and filing links. Preserve
OpenCorporates IDs and original registry links for follow-up.

## Failure modes

- Missing `OPENCORPORATES_API_KEY` should skip or fail cleanly, not fall back
  to scraping.
- 401/403 means token/access level problems.
- Jurisdiction codes are exact; a US state name is not a jurisdiction code.
- Aggregated records can lag or omit filings from the source registry.

## Evidence shape

`SearchResult.extras` should include jurisdiction code, company number,
company status, incorporation/current status dates when available, officers,
registered address, OpenCorporates URL, and original registry URL. `Source`
metadata should keep the same identifiers.

## Anti-patterns

- Do not treat OpenCorporates as the final authority when a state registry
  source URL is available.
- Do not use business entity filings as proof of candidate status.
- Do not run live jobs without confirming the API key/license constraints.
