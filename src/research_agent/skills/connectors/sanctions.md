---
name: sanctions
description: "OFAC sanctions screening with local SQLite cache plus legacy EU/UK rows; compliance-sensitive and freshness-critical."
when_to_use: "Name, alias, EIN, vessel, or entity screening against the local sanctions index when source freshness can be checked and cited."
when_not_to_use: "Final compliance determinations, stale UK/OFSI-only screening, unavailable EU bulk refreshes, or any task that needs legal advice."
---

# Sanctions connector

Use `sanctions_search` for sanctions-screening leads and citations to official
list entries. This connector is compliance-sensitive: a result is not a legal
determination, and a non-result is not clearance. Always inspect source
freshness and list authority before relying on output.

## Official documentation

- OFAC Sanctions List Service: https://ofac.treasury.gov/sanctions-list-service
- OFAC Advanced Sanctions List Standard FAQ: https://ofac.treasury.gov/sdn-list-data-formats-data-schemas/frequently-asked-questions-on-advanced-sanctions-list-standard
- OFAC compliance match guidance entry point: https://ofac.treasury.gov/ofac-compliance-hotline
- EU sanctions resources and Financial Sanctions Database pointer:
  https://finance.ec.europa.eu/eu-and-world/sanctions-restrictive-measures/overview-sanctions-and-related-resources_en
- UK Sanctions List current source and formats:
  https://www.gov.uk/government/publications/the-uk-sanctions-list
- UK single-list transition guidance:
  https://www.gov.uk/guidance/moving-to-a-single-list-for-uk-sanctions-designations-28-january-2026
- Legacy OFSI search closure page: https://sanctionssearchapp.ofsi.hmtreasury.gov.uk/

## Auth and cost

- Required env vars: none for normal use.
- Optional env vars:
  - `SANCTIONS_DB_PATH` overrides the local SQLite sanctions index path. Unset
    uses the module default under `data/sanctions.sqlite`.
- Cost: official OFAC/UK/EU list access is public, but the EU bulk path used
  by historical code may be unavailable or gated. Do not use scraped or
  third-party mirrors as authoritative replacements without a separate issue.
- Local/offline behavior: searches use the local SQLite index. If the cache is
  missing and source refresh fails, the connector can return empty results.
  Offline runs are useful only when `research doctor` or index metadata confirms
  a recent successful refresh for the list being searched.

## Required payload fields

- `query` - required common field; use a person, entity, alias, vessel, or ID.
- `sub_question` - required common field; state the list and match question.
- Connector-specific required fields: none.

## Knobs available

- `max_results` - optional client cap.
- `kinds` - optional list-kind filter. Valid values are `SDN`, `EU`, and `UK`.
  Use this only when the source freshness caveats below are acceptable.

## Valid payload examples

```yaml
kind: sanctions_search
payload:
  query: "Wagner Group"
  sub_question: "Screen Wagner Group against the current OFAC sanctions index."
  kinds:
    - SDN
  max_results: 5
```

```yaml
kind: sanctions_search
payload:
  query: "Abramovich"
  sub_question: "Look for legacy UK sanctions-index rows and verify freshness before use."
  kinds:
    - UK
  max_results: 5
```

## Request and pagination pattern

`sanctions_search` searches the local SQLite index using FTS first, then a
normalized fuzzy fallback. The index refresh path currently fetches OFAC
`sdn.xml` and parses the basic SDN schema. OFAC's Sanctions List Service is the
current official entry point for SDN and non-SDN list downloads; OFAC's FAQ
says the advanced XML files contain the same core list data and add metadata.

EU: the European Commission points users to the Financial Sanctions Database
for the consolidated list. The code keeps the historical FSD XML URL as a
fetchable source reference, but the refresh path is disabled because that bulk
endpoint has returned 403 in this project. Treat EU rows as stale unless a
successful refresh is proven.

UK: the UK Sanctions List is now the authoritative source for all UK sanctions
designations. The OFSI Consolidated List and legacy OFSI search page stopped
updating on 2026-01-28. Any local rows produced from the old OFSI feed are
reference-only for post-transition UK screening. Current UK work must cite the
UKSL formats at `https://sanctionslist.fcdo.gov.uk/docs/UK-Sanctions-List.*`.

## Failure modes

- Stale local index: check refresh metadata before using output. A fresh OFAC
  row and a stale UK/EU row have different evidentiary value.
- UK source transition: OFSI Consolidated List data after 2026-01-28 is stale
  for current UK designations. Use UKSL as the current authority.
- EU bulk access: prior unauthenticated bulk XML access can fail with 403.
  Do not interpret missing EU rows as no EU sanctions match.
- Fuzzy matches: fallback rows are leads and can be false positives. Confirm
  aliases, identifiers, dates of birth, addresses, vessels, or official IDs.
- Legal boundary: sanctions screening can support research, but final match
  decisions require the relevant regulator's guidance and human/legal review.

## Evidence shape

`SearchResult` rows use `source_kind="sanctions"`, official or local-detail
URLs, a matched name, snippet, and `extras` including `uid`, `list_kind`,
`sanctioning_agency`, `programs`, designation date, aliases, IDs, and `fuzzy`
when the fallback search produced the row.

`fetch()` resolves OFAC detail URLs through the local index, fetches OFAC Recent
Actions, or returns a bulk-list source summary for EU/UK list URLs. Cite the
official list source and retrieval timestamp. For UK, cite the current UKSL
format page, not the closed OFSI search, for current designations.

## Anti-patterns

- Do not treat a no-result response as sanctions clearance.
- Do not use stale OFSI rows as current UK sanctions evidence after
  2026-01-28.
- Do not hide list freshness, disabled EU refresh, or fuzzy-match status from
  synthesis.
- Do not use this connector for legal advice or outbound compliance action
  without human review.
