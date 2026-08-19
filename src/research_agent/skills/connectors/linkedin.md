---
name: linkedin
description: "LinkedIn person/company lookup through configured paid brokers (Proxycurl or Lix); use only when profile/company facts are necessary and spend is acceptable."
when_to_use: "person profiles, employment history, company headcount/industry/location facts, professional affiliations"
when_not_to_use: "ordinary web mentions -> web_search; corporate filings -> sos/opencorporates/edgar; avoid broad exploratory fan-out because each lookup can cost money"
---

# LinkedIn connector

`linkedin_search` uses a third-party broker because LinkedIn does not provide a public investigative API and direct scraping is blocked. The default broker is Proxycurl; set `LINKEDIN_BROKER=lix` to use Lix.

## Payload

- `query` - person name or company name.
- `sub_question` - what the downstream extraction should answer.
- `kind` - `person` (default) or `company`.
- `max_results` - default 10.

Examples:

```yaml
kind: linkedin_search
payload:
  query: "Sundar Pichai"
  sub_question: "What current and prior leadership roles are listed for Sundar Pichai?"
  kind: person
  max_results: 5
```

```yaml
kind: linkedin_search
payload:
  query: "Acme Robotics"
  sub_question: "What company profile facts does LinkedIn report for Acme Robotics?"
  kind: company
```

## Auth and cost

- Proxycurl: `LINKEDIN_BROKER=proxycurl`, `LINKEDIN_DATA_API_KEY`.
- Lix: `LINKEDIN_BROKER=lix`, `LIX_API_KEY`.
- Both brokers charge per lookup, commonly around $0.01-$0.05 per profile or company lookup.
- Missing broker credentials raise `MissingCredentialError`; the loop records a task failure instead of calling the broker.

## Use carefully

- Prefer `kind=person` for people and `kind=company` for organizations. The broker endpoints and output fields differ.
- Do not emit broad LinkedIn searches for every named entity in a run. Use it after cheaper sources show that profile facts matter.
- Do not auto-fetch every LinkedIn result. Fetch a profile only when the specific URL is needed to answer the sub-question.
- Treat broker data as a secondary source. Corroborate important claims with company pages, filings, archived bios, or news.

## Failure modes

- Invalid `kind` raises before the network call.
- Missing key fails loudly.
- Broker quota/rate-limit errors return no useful evidence; replan to public web or filings instead of retrying in a tight loop.
- Some profile fields can be stale or broker-normalized. Cite retrieval time and corroborate sensitive employment claims.
