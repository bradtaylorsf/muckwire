---
name: licensing
description: "State contractor/professional licensing lookup; CA CSLB is wired, TX/FL/NY are documented stubs."
when_to_use: "Checking contractor or professional license status, classifications, business identity, complaint disclosure, and license detail pages."
when_not_to_use: "BBB reputation, business entity filings, campaign finance, or legal case records."
---

# Licensing connector

Use `licensing_search` for official licensing-board lookups. The current
implementation supports California CSLB. Texas, Florida, and New York entries
are registry stubs and should return unsupported until selectors are built.

## Official documentation

- California CSLB Check a License: https://cslb.ca.gov/OnlineServices/CheckLicenseII/CheckLicense.aspx
- CSLB Online Services: https://www.cslb.ca.gov/OnlineService.aspx
- Texas TDLR license search entry: https://license.state.tx.us/search/
- Florida DBPR license search: https://www.myfloridalicense.com/wl11.asp?SID+=&mode=0
- Florida verify-a-license instructions: https://www2.myfloridalicense.com/how-to-verify-a-license/
- New York DOS Licensing Services: https://dos.ny.gov/licensing/index.html
- New York DOS business-name license search: https://appext20.dos.ny.gov/lcns_public/bus_name_search_frm

## Auth and cost

No auth and no paid API for the supported CSLB workflow. The connector uses
Playwright and should keep conservative per-host pacing.

## Required payload fields

- `query` - required common field; use license number or business/person name.
- `sub_question` - required common field.

## Knobs available

- `state` - `CA` is supported; `TX`, `FL`, and `NY` are stubs until recipes are
  implemented.
- `max_results` - optional client cap.

## Valid payload examples

```yaml
kind: licensing_search
payload:
  query: "SBI Builders"
  sub_question: "What official CSLB license status and classifications exist for SBI Builders?"
  state: "CA"
  max_results: 5
```

## Request and pagination pattern

For California, the connector uses CSLB Check a License tabs for license
number, business-name, and personnel-name searches. Detail pages can expose
license status, classifications, business type/address, bonds, workers
compensation, personnel, and complaint disclosure links. CSLB notes that the
database is unavailable Sundays 8 p.m. through Monday 6 a.m. for maintenance.

TX/FL/NY official lookup entry points are documented above but not automated.
Do not emit them as successful evidence until state recipes exist.

## Failure modes

- CSLB maintenance window, blocked Playwright access, or missing ASP.NET
  postback fields should be reported as blocked/unsupported, not no-result.
- Searches returning more than CSLB's visible row cap need narrower queries.
- TX/FL/NY stubs are unsupported implementation gaps.
- License status is not a performance review; cross-check BBB/reviews only as
  separate context.

## Evidence shape

`SearchResult.extras` should include license number, business name, state,
status, classification, profile URL, and `source_kind="licensing"`. `Source`
metadata should preserve status, classifications, bond/workers-comp fields,
complaint disclosure notes, and the official board URL.

## Anti-patterns

- Do not use BBB as a substitute for official licensing records.
- Do not treat a missing CSLB result during maintenance as proof of no license.
- Do not claim TX/FL/NY support until the connector has working selectors.
