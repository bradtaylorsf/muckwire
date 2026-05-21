---
name: nonprofits
description: "ProPublica Nonprofit Explorer API v2 for IRS Form 990 nonprofit profiles and filings."
when_to_use: "US nonprofit lookup by name or EIN, Form 990 summaries, revenue/assets/compensation context, and filing PDF/XML links."
when_not_to_use: "For-profit companies, state charity registrations, campaign committees, or lobbying filings."
---

# Nonprofits connector

Use `nonprofits_search` for IRS-recognized nonprofit organizations in
ProPublica Nonprofit Explorer. It is best for Form 990 profile and filing
context, not real-time corporate or campaign-finance records.

## Official documentation

- Nonprofit Explorer API v2: https://projects.propublica.org/nonprofits/api/
- Nonprofit Explorer product page: https://projects.propublica.org/nonprofits/
- ProPublica data terms: https://www.propublica.org/about/propublica-data-terms-of-use

## Auth and cost

No key is required. The API is free subject to ProPublica terms. It accepts
GET requests under `https://projects.propublica.org/nonprofits/api/v2`.

## Required payload fields

- `query` - required common field; use organization name or EIN.
- `sub_question` - required common field.

## Knobs available

- `max_results` - optional client cap.

## Valid payload examples

```yaml
kind: nonprofits_search
payload:
  query: "Heritage Foundation"
  sub_question: "What Nonprofit Explorer profile and recent Form 990 filings exist for Heritage Foundation?"
  max_results: 10
```

## Request and pagination pattern

Search uses `/search.json` and can return paginated organization results.
Profile fetches use `/organizations/:ein.json`. The API supports state and
taxonomy filters, but the current connector exposes only the common query and
result cap. Replan with an EIN when a search result needs exact disambiguation.

## Failure modes

- Nonprofit Explorer excludes some very small e-Postcard organizations.
- Data reflects IRS processing and ProPublica updates; it is not real-time.
- Name search can match alternate names and city text; verify EIN before
  merging entities.

## Evidence shape

`SearchResult.extras` should preserve EIN, organization name, city/state,
NTEE/category, ruling/subsection codes, latest tax period, and filing links.
`fetch()` should return `Source.cleaned_text` summarizing profile and filings,
with metadata containing EIN and source URLs.

## Anti-patterns

- Do not use this connector for PACs or candidate committees; use `fec_search`.
- Do not infer current operations solely from an old Form 990.
- Do not merge organizations with similar names without matching EINs.
