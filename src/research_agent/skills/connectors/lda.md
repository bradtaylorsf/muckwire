---
name: lda
description: "Lobbying Disclosure Act filings, registrants, clients, and LD-203 contributions from LDA.gov."
when_to_use: "Federal lobbying registrations, quarterly LD-2 activity, registrant/client lookup, and LD-203 political contribution filings."
when_not_to_use: "Campaign finance transactions outside LD-203, state lobbying, or federal contracts; use fec_search, state portals, or usaspending_search."
---

# LDA connector

Use `lda_search` for the federal Lobbying Disclosure Act database. It covers
LD-1 registrations, LD-2 quarterly lobbying activity, and LD-203 contribution
reports. LDA rows are disclosures, not proof that a policy position succeeded.

## Official documentation

- LDA.gov Download API page: https://lda.gov/api/
- LDA.gov public search home: https://lda.gov/
- Senate legacy API documentation and migration notice: https://lda.senate.gov/api/redoc/v1/

The Senate page says the legacy site will no longer be available after
2026-06-30 and directs systems to LDA.gov.

## Auth and cost

The API key registration link is on the LDA.gov API page. Anonymous access can
work at low volume, but authenticated access should be used for long jobs when
`LDA_API_KEY` is configured. The connector sends a token when available.

## Required payload fields

- `query` - required common field; use a registrant, client, lobbyist, issue,
  or organization name.
- `sub_question` - required common field.

## Knobs available

- `kind` - `filings` (default), `registrants`, or `contributions`.
- `max_results` - optional client cap.

## Valid payload examples

```yaml
kind: lda_search
payload:
  query: "Heritage Foundation"
  sub_question: "What federal lobbying filings or registrants mention Heritage Foundation?"
  kind: "filings"
  max_results: 10
```

## Request and pagination pattern

Use `kind=registrants` to resolve a formal registrant/client identity, then
`kind=filings` for LD-1/LD-2 activity and `kind=contributions` for LD-203.
The API is paginated; keep `max_results` bounded and fan out only from rows
with stable filing or registrant URLs/IDs.

## Failure modes

- 401/403 means an API token is missing, invalid, or rate-limited.
- Legacy `lda.senate.gov` links should be treated as transitional because of
  the 2026-06-30 migration notice.
- Names are formal and can differ from common names; try affiliates and legal
  entities before declaring a gap.

## Evidence shape

`SearchResult.extras` should preserve filing IDs, registrant/client names,
filing type, filing year/period, amount fields for LD-203, and source URLs.
`fetch()` should return a `Source` with `source_kind="lda"` and markdown
sections that make LD-1/LD-2/LD-203 distinctions clear.

## Anti-patterns

- Do not use LDA for FEC donor transactions; use `fec_search`.
- Do not merge LD-1 registration, LD-2 activity, and LD-203 contributions into
  a single undifferentiated claim.
- Do not rely on legacy Senate URLs without checking LDA.gov availability.
