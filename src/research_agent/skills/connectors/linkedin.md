---
name: linkedin
description: "Paid LinkedIn person/company lookup via broker; Proxycurl is shut down, Lix remains code-supported but gated."
when_to_use: "Narrow people or company discovery when an operator has explicitly approved a paid LinkedIn-data broker and the result will be treated as a lead."
when_not_to_use: "Automatic broad sweeps, local/offline runs, compliance decisions, or cases where a public primary source can prove the same fact."
---

# LinkedIn connector

Use `linkedin_search` only after confirming that paid/gated broker access is
allowed for the job. LinkedIn profile data is third-party broker evidence, not
an official record. Prefer official biographies, filings, employer pages, court
records, campaign records, or `web_search` before spending broker credits.

## Official documentation

- Proxycurl shutdown status: https://nubela.co/proxycurl/auth/register.html
- Proxycurl 2026 status and NinjaPear successor note: https://nubela.co/blog/what-is-proxycurl-api-now-in-2026-im-the-founder/
- Proxycurl shutdown notice: https://nubela.co/blog/goodbye-proxycurl/
- NinjaPear API reference and pricing, for successor context not implemented by this connector: https://nubela.co/docs and https://nubela.co/pricing
- Lix API reference: https://lix-it.com/docs/
- Lix LinkedIn API pricing/status page: https://lix-it.com/pages/linkedin-api
- Lix terms: https://lix-it.com/terms?currency=usd

## Auth and cost

- Required env vars:
  - `LINKEDIN_BROKER` selects the broker recipe. Valid values in code are
    `proxycurl` and `lix`; unset defaults to `proxycurl`.
  - `LINKEDIN_DATA_API_KEY` is read when `LINKEDIN_BROKER=proxycurl`.
  - `LIX_API_KEY` is read when `LINKEDIN_BROKER=lix`.
- Proxycurl: official Nubela pages say Proxycurl is no longer in service.
  Do not assume the default `proxycurl` recipe is healthy. Run it only for a
  deliberate legacy account test where the operator has confirmed access.
- NinjaPear: official successor path from the Proxycurl founder, but this
  connector does not implement NinjaPear endpoints. Do not set
  `LINKEDIN_BROKER=ninjapear` unless code is added.
- Lix: paid/gated. Lix documents Standard Credits and 1 credit per LinkedIn
  API call. Use only with operator-approved budget and terms review.
- Anonymous/local behavior: there is no anonymous or offline fallback. Missing
  broker keys raise a missing-credential error or cause smoke to skip/fail.

## Required payload fields

- `query` - required common field; use a specific person or company name.
- `sub_question` - required common field; state what the LinkedIn lead should
  help prove.
- Connector-specific required fields: none.

## Knobs available

- `kind` - optional; valid values are `person` and `company`; default is
  `person`.
- `max_results` - optional client cap. Keep it small because each broker call
  can spend credits and create terms risk.

## Valid payload examples

```yaml
kind: linkedin_search
payload:
  query: "Sundar Pichai"
  sub_question: "Find a LinkedIn person-profile lead for Sundar Pichai."
  kind: person
  max_results: 3
```

```yaml
kind: linkedin_search
payload:
  query: "Anthropic"
  sub_question: "Find the LinkedIn company-profile lead for Anthropic."
  kind: company
  max_results: 3
```

## Request and pagination pattern

The connector resolves the configured broker, sends one person or company
search request, and returns up to `max_results` rows. Fetch accepts
`https://www.linkedin.com/in/...` and `https://www.linkedin.com/company/...`
URLs and asks the same broker for profile/company enrichment.

For Lix, the code-supported search recipes use LinkedIn search endpoints under
`https://api.lix-it.com/v1/li/linkedin/search/...` with an `Authorization`
header. Lix documents person and organization search as one Standard Credit per
call, with response paging metadata in the broker response. The current
connector does not expose an explicit page or pagination-token payload knob.

## Failure modes

- Proxycurl shutdown: official status pages say it is no longer in service.
  Treat `proxycurl` failures as expected unless an operator confirms a working
  legacy account.
- Legal/terms risk: LinkedIn has no public API for these lookups. Do not run
  automatic broad discovery, do not bypass account protections, and do not
  use broker data as the sole basis for an adverse or compliance claim.
- Missing credentials: do not silently fall back to web scraping.
- Rate limits or broker errors: retry only with explicit backoff and only if
  the job still has approval to spend credits.
- True no-result behavior: use official or public web sources before assuming
  the person/company lacks a profile.

## Evidence shape

`SearchResult` rows use `source_kind="linkedin"`, a LinkedIn URL, title,
snippet, and `extras` containing `kind`, `broker`, and person/company fields
such as location, current company/title, industry, headcount, or HQ location.

`fetch()` returns `Source.cleaned_text` as a markdown profile or company
summary and `metadata` with broker, kind, profile URL, and parsed facts. Cite
it as broker-derived context only. Corroborate employment, affiliation,
headcount, and titles against primary or public sources before synthesis.

## Anti-patterns

- Do not use `linkedin_search` in local/offline runs or unbudgeted loops.
- Do not imply Proxycurl is healthy in 2026; official pages say it is shut
  down and NinjaPear is not a drop-in replacement implemented here.
- Do not auto-fetch every LinkedIn URL found by web search.
- Do not treat profile data as an official identity, employment, or sanctions
  record.
