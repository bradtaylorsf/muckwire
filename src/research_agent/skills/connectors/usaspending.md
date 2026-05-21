---
name: usaspending
description: "USAspending.gov API v2 federal award search for contracts, grants, and loans."
when_to_use: "Federal awards, recipient spending, agency funding, contract/grant/loan discovery, and award-detail follow-up."
when_not_to_use: "Lobbying disclosures, campaign finance, state/local awards, or procurement opportunities before award."
---

# USAspending connector

Use `usaspending_search` for federal award data after money has been obligated.
It is useful for recipient, agency, NAICS/PSC, and award-detail research.

## Official documentation

- API documentation index: https://api.usaspending.gov/docs/
- Endpoint list: https://api.usaspending.gov/docs/endpoints
- USAspending site: https://www.usaspending.gov/

## Auth and cost

No authorization is currently required by the public API docs. The connector
uses polite rate limiting.

## Required payload fields

- `query` - required common field; use recipient, agency, award term, UEI, or
  contract/grant keyword.
- `sub_question` - required common field.

## Knobs available

- `award_type` - `contracts` (default), `grants`, or `loans`.
- `max_results` - optional client cap.

## Valid payload examples

```yaml
kind: usaspending_search
payload:
  query: "Heritage Foundation contract"
  sub_question: "What federal USAspending awards mention Heritage Foundation?"
  award_type: "contracts"
  max_results: 10
```

## Request and pagination pattern

The connector uses API v2 award search endpoints such as
`/api/v2/search/spending_by_award/`, which accept POST filter bodies. Keep
filters explicit: award type bucket, recipient/keyword search text, time
period, agency, NAICS/PSC, or location. Paginated responses should preserve
award IDs so `fetch()` can retrieve `/api/v2/awards/<AWARD_ID>/`.

## Failure modes

- 400 usually means a malformed POST filter, often missing time period or an
  invalid award-type code.
- 500/timeout should be retried with backoff.
- Award records can be revised; preserve the retrieval timestamp and last
  updated fields when available.
- Recipient names and UEIs can change; avoid merging recipients by name alone.

## Evidence shape

`SearchResult.extras` should include award ID/PIID/FAIN/URI, recipient name,
UEI when present, awarding/funding agency, award type, obligation amount,
period of performance, NAICS/PSC, and generated USAspending URL. `fetch()`
should render a `Source` with award detail metadata and raw API fields needed
for audit.

## Anti-patterns

- Do not use USAspending for open solicitations; use SAM.gov or a future
  procurement connector.
- Do not equate obligations with payments.
- Do not treat a recipient-name match as entity resolution without UEI/CAGE or
  address confirmation.
