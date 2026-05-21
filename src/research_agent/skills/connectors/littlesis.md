---
name: littlesis
description: "LittleSis power-map entities and relationships; useful leads, not final evidence."
when_to_use: "Discovering people, organizations, board seats, donations, family ties, and relationship leads to verify elsewhere."
when_not_to_use: "When the task needs primary-source proof, official filings, sanctions, contracts, or exhaustive rosters."
---

# LittleSis connector

Use `littlesis_search` to discover relationship leads between people and
organizations. LittleSis is a power-mapping database with useful provenance,
but rows should be verified against original filings or pages before final
synthesis.

## Official documentation

- LittleSis API documentation: https://dev.littlesis.org/api/
- Public API entry: https://littlesis.org/api
- Bulk data note: https://littlesis.org/bulk_data

## Auth and cost

No API key is required for normal API use. Requests may be rate-limited. Bulk
dataset access is separate from this connector.

## Required payload fields

- `query` - required common field; use a person, organization, or formal name.
- `sub_question` - required common field.

## Knobs available

- `kind` - `entities` (default) or `relationships`.
- `max_results` - optional client cap.

## Valid payload examples

```yaml
kind: littlesis_search
payload:
  query: "Peter Thiel"
  sub_question: "What LittleSis entity or relationship leads exist for Peter Thiel?"
  kind: "entities"
  max_results: 10
```

## Request and pagination pattern

Start with `kind=entities` to resolve the LittleSis ID and canonical page.
Use relationship endpoints for known IDs when a follow-up needs board seats,
donations, family ties, ownership, or position links. Relationship categories
carry IDs and names; preserve both because category semantics matter.

## Failure modes

- Ambiguous names can return many similarly named entities; use location,
  employer, or aliases in follow-up queries.
- Relationship direction can vary; check whether the target is `entity1` or
  `entity2` before labeling counterparties.
- Missing data is not a confirmed absence of a relationship.

## Evidence shape

`SearchResult` rows should include LittleSis URLs, entity or relationship IDs,
relationship category, counterpart names, dates, amount when present, and
provenance hints in `extras`. `Source.metadata` should preserve the API
resource type, IDs, and LittleSis page URL.

## Anti-patterns

- Do not cite LittleSis alone for a high-stakes allegation.
- Do not assume all relationship counterparts are organizations.
- Do not infer current status when `is_current` or dates are null.
