---
name: scholar
description: "Google Scholar through SerpAPI for legal case leads and scholarly result discovery; paid API key required."
when_to_use: "Case-law discovery through Google Scholar or a targeted scholarly search where OpenAlex/CourtListener do not cover the need."
when_not_to_use: "Broad academic literature reviews that OpenAlex can answer for free, primary court records available from CourtListener, or local/offline runs without SERPAPI_KEY."
---

# Scholar connector

Use `scholar_search` for Google Scholar result discovery through SerpAPI. It is
a paid/keyed connector and should be treated as a lead generator. Fetch the
result URL or a primary source before relying on any claim in synthesis.

## Official documentation

- SerpAPI Google Scholar API: https://serpapi.com/google-scholar-api
- SerpAPI pricing: https://serpapi.com/pricing
- SerpAPI terms: https://serpapi.com/legal
- OpenAlex connector skill for the preferred free scholarly path:
  `src/research_agent/skills/connectors/openalex.md`

## Auth and cost

- Required env vars:
  - `SERPAPI_KEY` is required for every live `scholar_search` call.
- Paid constraints: SerpAPI requires a private API key and bills searches
  against the operator's plan. Cached SerpAPI hits may be free under SerpAPI's
  cache policy, but the connector should still be planned as paid/gated.
- Anonymous/local behavior: no anonymous fallback exists. In `--local` model
  mode the connector still needs `SERPAPI_KEY`; local LLM routing does not make
  Google Scholar local or free.

## Required payload fields

- `query` - required common field; use a compact Google Scholar query.
- `sub_question` - required common field; state what the Scholar hit should
  help prove.
- Connector-specific required fields: none.

## Knobs available

- `kind` - optional; valid values are `case_law` and `articles`; default is
  `case_law`.
- `max_results` - optional client cap. SerpAPI documents `num` as 1-20 for
  the Google Scholar engine; the connector clamps the request to 20.

## Valid payload examples

```yaml
kind: scholar_search
payload:
  query: "Section 230 appellate immunity platform moderation"
  sub_question: "Find Google Scholar case-law leads on Section 230 moderation immunity."
  kind: case_law
  max_results: 5
```

```yaml
kind: scholar_search
payload:
  query: "unitary executive theory Project 2025"
  sub_question: "Find scholarly article leads on unitary executive theory and Project 2025."
  kind: articles
  max_results: 10
```

## Request and pagination pattern

The connector calls SerpAPI with `engine=google_scholar`, `q=<query>`,
`api_key=<SERPAPI_KEY>`, and `num=min(max_results, 20)`. For `kind=case_law`,
the connector adds `as_sdt=2006`, which is the current code path for legal
case results. For `kind=articles`, the connector omits `as_sdt`.

SerpAPI also documents `start` for pagination and `no_cache=true` to force a
fresh fetch when an exact cached search exists. The current registry contract
does not expose `start` or `no_cache`; do not promise pagination or minute-level
freshness from planner payloads until those knobs are added.

## Failure modes

- Missing `SERPAPI_KEY`: reject the task or surface the missing credential.
- Paid quota exhausted: stop automatic retries and prefer free/open connectors.
- Cache freshness: SerpAPI says exact cached searches can be served for up to
  one hour unless `no_cache=true`; this connector does not currently expose
  `no_cache`.
- Empty results: simplify the query, try `kind=articles`, or use
  `openalex_search`; do not synthesize absence of scholarship from one empty
  Google Scholar call.
- Legal source authority: Google Scholar legal hits are discovery leads. Use
  `courtlistener_search` or official court sources for primary case text when
  available.

## Evidence shape

`SearchResult` rows use `source_kind="scholar"` with Scholar or publisher
URLs, titles, snippets, optional publication year, and `extras` such as
`kind`, citation links, publication info, and PDF links when SerpAPI returns
them.

`fetch()` returns a `Source` from the selected Scholar result URL. PDFs are
extracted through the PDF tool; HTML is extracted with readability/trafilatura.
Treat Scholar metadata as a lead until the fetched source is available.

## Anti-patterns

- Do not use `scholar_search` for broad scholarly sweeps when
  `openalex_search` can provide free structured metadata and OA URLs.
- Do not run `scholar_search` automatically in unbudgeted local jobs.
- Do not treat cached Scholar result snippets as current legal authority.
- Do not cite a Scholar result row when the actual opinion, article, or PDF can
  be fetched.
