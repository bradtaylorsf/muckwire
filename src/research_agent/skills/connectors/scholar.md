---
name: scholar
description: "Google Scholar through SerpAPI for case-law and article discovery; requires SERPAPI_KEY and incurs per-query cost."
when_to_use: "case-law discovery, Google Scholar article search, citation-oriented research, legal/scholarly source discovery when OpenAlex or CourtListener is insufficient"
when_not_to_use: "free scholarly metadata first pass -> openalex; court opinions with known court/citation -> courtlistener; broad web context -> web_search"
---

# Scholar connector

`scholar_search` uses SerpAPI's Google Scholar engine. Use it when Google Scholar coverage is specifically valuable and paid search is acceptable.

## Payload

- `query` - case citation, case name, article title, author/topic phrase, or legal/scholarly concept.
- `sub_question` - what the downstream extraction should answer.
- `kind` - `case_law` (default) or `articles`.
- `max_results` - default 20; SerpAPI's Scholar endpoint caps one call at 20.

Examples:

```yaml
kind: scholar_search
payload:
  query: "Section 230 appellate"
  sub_question: "Which recent appellate cases discuss Section 230 immunity?"
  kind: case_law
  max_results: 10
```

```yaml
kind: scholar_search
payload:
  query: "unitary executive theory Project 2025"
  sub_question: "Which scholarly articles analyze Project 2025 and unitary executive theory?"
  kind: articles
```

## Auth and cost

- Requires `SERPAPI_KEY`.
- The connector uses `engine=google_scholar`; `kind=case_law` adds `as_sdt=2006`.
- SerpAPI bills per search. The connector code documents roughly $0.015/search on the 5k/month plan, but operators should treat current vendor pricing as authoritative.
- Missing credentials raise `MissingCredentialError`; the loop records a structured task failure.

## Use carefully

- Prefer `openalex_search` for free scholarly metadata and open-access discovery before spending SerpAPI calls.
- Prefer `courtlistener_search` for known legal citations, courts, or docket/opinion searches.
- Do not cite a Scholar search result as the source text. Fetch the result URL or linked PDF before making substantive claims.
- Use date/court/topic terms in the query; Scholar ranking can bury current material under older, highly cited records.

## Failure modes

- Invalid `kind` raises before a paid call.
- Missing key fails loudly.
- Some result links point to paywalled PDFs or publisher pages; fetch may return metadata only. Replan to open-access URLs, CourtListener, OpenAlex, or web search when full text is unavailable.
