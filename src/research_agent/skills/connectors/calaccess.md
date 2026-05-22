---
name: calaccess
description: "California Cal-Access and Power Search campaign finance records for contributions and independent expenditures."
when_to_use: "California state campaign contributions, candidate/committee campaign finance, ballot-measure committees, and independent expenditures."
when_not_to_use: "Federal FEC filings, lobbying records not implemented by the connector, business entities, or non-California campaign finance."
---

# Cal-Access connector

Use `calaccess_search` for California Secretary of State campaign-finance
searches. Power Search and Cal-Access are official California disclosure
surfaces, but the connector currently automates only contributions and
independent expenditures.

## Official documentation

- California Power Search: https://powersearch.sos.ca.gov/
- Power Search FAQ: https://powersearch.sos.ca.gov/frequently-asked-questions/
- Power Search help: https://powersearch.sos.ca.gov/help/
- Cal-Access FAQ for candidates, committees, and entities: https://www.sos.ca.gov/campaign-lobbying/cal-access-resources/cal-access-users-manual/campaign-finance-faq-table-contents-section-1/cal-access-faqs-s1-q7

## Auth and cost

No auth and no paid API. The connector uses Playwright against public
Secretary of State pages with a conservative rate gate.

## Required payload fields

- `query` - required common field; use candidate, committee, donor, payee, or
  ballot-measure terms.
- `sub_question` - required common field.

## Knobs available

- `kind` - `contributions` (default) or `independent_expenditures`.
- `max_results` - optional client cap.

## Valid payload examples

```yaml
kind: calaccess_search
payload:
  query: "Newsom"
  sub_question: "What California Power Search contribution records mention Newsom?"
  kind: "contributions"
  max_results: 10
```

## Request and pagination pattern

Power Search contributions use server-rendered forms and result tables.
Independent expenditures use a separate Power Search service. Cal-Access
legacy pages cover more campaign-finance and lobbying data, but lobbying is
not automated here. For candidate/committee/entity discovery, use Cal-Access
or Power Search as the official source, then fetch detail pages for amounts,
dates, parties, and filing references.

## Failure modes

- A maintenance page, frame-only legacy page, or empty SPA shell is not a true
  no-result.
- `kind=lobbying` is intentionally unsupported until a separate recipe lands.
- Selector drift should produce diagnostics rather than fabricated rows.
- Search results may omit rolled-up totals; fetch detail pages before citing.

## Evidence shape

`SearchResult.extras` should preserve contributor/payee, recipient/committee,
amount, date, committee IDs, office/ballot-measure fields, filing reference,
and `source_kind="calaccess"`. `Source.cleaned_text` should render the rolled
up record and detail-page provenance.

## Anti-patterns

- Do not use Cal-Access for federal candidate filing status; use `fec_search`.
- Do not use `sos_search`; in this repo it means business filings, not
  campaign finance.
- Do not treat a selector miss as a confirmed disclosure gap.
