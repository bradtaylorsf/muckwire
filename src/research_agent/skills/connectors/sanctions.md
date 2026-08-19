---
name: sanctions
description: "OFAC SDN and UK OFSI sanctions screening through a local SQLite/FTS index; no auth, compliance-sensitive, with EU refresh currently disabled."
when_to_use: "sanctions screening, OFAC SDN checks, UK OFSI checks, aliases, passports, EINs, designation programs"
when_not_to_use: "general adverse media -> gdelt/news/web_search; corporate registry facts -> opencorporates/sos; legal case history -> courtlistener"
---

# Sanctions connector

`sanctions_search` searches a local SQLite/FTS index built from official sanctions bulk files. `sanctions_fetch` opens canonical details or bulk-list URLs.

## Payload

- `query` - person, organization, vessel, aircraft, alias, EIN, passport, or other identifier.
- `sub_question` - what the downstream extraction should answer.
- `max_results` - default 20.
- `kinds` - optional list of list kinds, currently useful as `["SDN"]`, `["UK"]`, or `["SDN", "UK"]`.

Example:

```yaml
kind: sanctions_search
payload:
  query: "Wagner Group"
  sub_question: "Is Wagner Group listed on OFAC or UK sanctions lists, and under what programs?"
  kinds: [SDN, UK]
  max_results: 10
```

## Sources and freshness

- OFAC SDN XML: `https://www.treasury.gov/ofac/downloads/sdn.xml`.
- UK OFSI consolidated CSV: `https://ofsistorage.blob.core.windows.net/publishlive/2022format/ConList.csv`.
- EU consolidated list refresh is intentionally disabled because the former public bulk endpoint now returns 403; doctor surfaces this as a skip.
- The local index refreshes when stale, with a 24-hour TTL. `SANCTIONS_DB_PATH` can relocate the dedicated `sanctions.sqlite` database.

## Interpretation rules

- A hit is a screening lead, not a final legal conclusion. Match name, aliases, identifiers, country, program, and source URL before making claims.
- Prefer exact identifiers when available. Names alone can produce false positives.
- Use `kinds` when a question asks about a specific list to avoid mixing OFAC and UK evidence.

## Failure modes

- Network failures during refresh leave the previous local index in place when available.
- EU data is unavailable through the disabled refresh path; report the gap instead of implying EU clearance.
- Empty results mean no match in the local indexed lists, not absence from every sanctions regime worldwide.
