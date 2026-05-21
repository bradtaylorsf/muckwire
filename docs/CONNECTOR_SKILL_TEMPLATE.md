---
name: connector-short-name
description: "One-line planner routing signal for this connector."
when_to_use: "Research situations where this connector is the right first source."
when_not_to_use: "Nearby questions that should use another connector or generic web search."
---

# Connector display name

Use `<short_name>_search` for the connector's authoritative scope. Keep usage
guidance here; registry schemas enforce only the minimum payload contract.

## Official documentation

- API or site docs:
- Terms, usage policy, or robots guidance:
- Migration or maintenance notices to verify before changing code:

## Auth and cost

- Required env vars:
- Free/paid constraints:
- Anonymous fallback behavior:

## Required payload fields

- `query` - required common field.
- `sub_question` - required common field.
- Connector-specific required fields:

## Knobs available

- `kind` - valid modes and defaults.
- `max_results` - default and cap.
- Other connector-specific fields:

## Valid payload examples

```yaml
kind: <short_name>_search
payload:
  query: "example query"
  sub_question: "What should this connector prove?"
```

## Request and pagination pattern

Describe endpoint/page entry, filters, pagination, detail-page fan-out, and
rate limits. Include stable selectors only when they are reliable enough to
survive ordinary site changes.

## Failure modes

- Missing credentials:
- Rate limits/captcha/blocked access:
- Maintenance windows:
- True no-result behavior:
- Retry/backoff guidance:

## Evidence shape

Describe expected `SearchResult` fields and which connector-specific values
belong in `extras`. For fetch support, describe expected `Source.cleaned_text`
sections and `metadata` fields.

## Anti-patterns

- Do not use this connector outside its source authority.
- Do not treat third-party profile/context pages as official records unless
  the connector itself is an official registry.
