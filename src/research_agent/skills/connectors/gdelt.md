---
name: gdelt
description: "GDELT DOC 2.0 news discovery for broad article/event coverage with no auth."
when_to_use: "Broad news/event discovery, media coverage timelines, and finding article URLs across countries or languages."
when_not_to_use: "Primary government records, court filings, company filings, or source-specific registries; use the direct official connector first."
---

# GDELT connector

Use `gdelt_search` for broad news discovery when a query should surface many
publishers quickly. Treat it as discovery and context, not as the final
authority for a factual claim.

## Official documentation

- GDELT DOC 2.0 API overview: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/amp/
- DOC API base used by the connector: `https://api.gdeltproject.org/api/v2/doc/doc`
- GDELT data/codebooks landing pages: https://www.gdeltproject.org/data.html

## Auth and cost

No key is required. The connector rate-limits itself; keep broad sweeps polite
because DOC API traffic goes to public GDELT infrastructure.

## Required payload fields

- `query` - required common field; use a compact news query.
- `sub_question` - required common field; state what the coverage should prove.

## Knobs available

- `since` - optional `YYYY-MM-DD` lower bound; narrows the DOC API time window.
- `language` - optional language filter such as `english`.
- `max_results` - optional client cap.

## Valid payload examples

```yaml
kind: gdelt_search
payload:
  query: "Project 2025 mainstream coverage"
  sub_question: "Which mainstream outlets covered Project 2025 recently?"
  since: "2026-01-01"
  language: "english"
  max_results: 10
```

## Request and pagination pattern

The connector uses DOC 2.0 article-list style requests and returns article
URLs. Use GDELT query operators only when they are necessary: quoted phrases,
`nearN:"word otherword"` proximity, domain/source filters, and language/date
filters. Keep the first query broad, then replan with publisher names or
specific claims discovered in results.

## Failure modes

- Empty results often mean the query is too narrative; shorten it.
- HTTP 429/5xx or timeouts should be retried with backoff.
- DOC results can include syndication, duplicates, and secondary writeups.
- GDELT is not an archive guarantee; fetch article URLs promptly.

## Evidence shape

`SearchResult` rows should contain the article URL, title, snippet or source
metadata, published timestamp when available, `source_kind="gdelt"`, and
extras such as source country/language/domain when returned. Fetch follows the
normal `web_fetch` path; cite the fetched article, not just the GDELT row.

## Anti-patterns

- Do not use GDELT when an official connector exists for the same fact.
- Do not treat GDELT mention volume as proof of event truth.
- Do not use long natural-language paragraphs as DOC queries.
