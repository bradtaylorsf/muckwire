---
name: bbb
description: "BBB business profiles, ratings, accreditation, complaints, and alerts; private nonprofit context, not government authority."
when_to_use: "Business reputation context, complaint history, BBB accreditation/rating, and profile discovery for companies or contractors."
when_not_to_use: "Official licensing, legal status, corporate filings, sanctions, or government enforcement records."
---

# BBB connector

Use `bbb_search` for Better Business Bureau profile context. BBB is a private nonprofit
marketplace-trust organization, not a government licensing authority.
Treat BBB profiles as reputation/context evidence and cross-check official
licensing or registry facts elsewhere.

## Official documentation

- BBB homepage/search entry: https://www.bbb.org/
- About BBB and profile/rating/accreditation behavior: https://www.bbb.org/all/about-bbb/
- Complaint process: https://www.bbb.org/process-of-complaints-and-reviews/complaints
- BBB FAQ: https://www.bbb.org/frequently-asked-questions

## Auth and cost

No auth and no public API. The connector uses Playwright against public BBB
pages with a conservative per-host rate gate.

## Required payload fields

- `query` - required common field; use business name plus city/state when known.
- `sub_question` - required common field.

## Knobs available

- `max_results` - optional client cap.

## Valid payload examples

```yaml
kind: bbb_search
payload:
  query: "SBI Builders San Jose"
  sub_question: "What BBB profile, rating, accreditation, and complaint context exists for SBI Builders?"
  max_results: 5
```

## Request and pagination pattern

The connector starts at BBB search with business name/location terms, reads
result cards, then fetches profile pages. Profiles can expose rating,
accreditation, business details, complaint counts, complaint categories,
reviews, alerts, and government-action notes. BBB pages are regional; include
city/state to avoid merging branch profiles.

## Failure modes

- Captcha, bot-blocking, or a blank React render means blocked access, not a
  true no-result.
- Result cards without profile links should be skipped.
- Ratings and accreditation are separate; accreditation is voluntary.
- Complaint text can be behind reveal controls; fetch should click stable show
  more buttons when possible.

## Evidence shape

`SearchResult.extras` should include rating, accreditation status, location,
profile URL, complaint counts when visible, and `source_kind="bbb"`. `Source`
metadata should preserve rating, accreditation, complaint counts, categories,
and government-action snippets.

## Anti-patterns

- Do not cite BBB as proof that a contractor is licensed.
- Do not treat a high rating as proof there are no legal or licensing issues.
- Do not compare complaint counts without considering company size and volume.
