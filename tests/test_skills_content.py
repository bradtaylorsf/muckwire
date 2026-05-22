"""Validate the shipped connector and strategy skill markdown content.

Loader behavior is covered in ``test_skills_loader.py``; this file validates
the *content* of the 5 initial connector skills (congress, edgar, fedregister,
courtlistener, fec) and the shipped strategy skills — frontmatter completeness,
presence of required body sections, and that any knobs the skill names match
the connector's actual ``search()`` signature.
"""

from __future__ import annotations

import importlib
import inspect
import re

import pytest
import yaml

from research_agent.skills import loader as skills_loader
from research_agent.skills.loader import clear_cache, list_skills, load_skill

CONNECTOR_SKILLS = ("congress", "edgar", "fedregister", "courtlistener", "fec")
ISSUE_318_CONNECTOR_SKILLS = (
    "gdelt",
    "lda",
    "littlesis",
    "nonprofits",
    "opencorporates",
    "usaspending",
)
ISSUE_319_CONNECTOR_SKILLS = ("bbb", "calaccess", "licensing")
ISSUE_320_CONNECTOR_SKILLS = ("linkedin", "scholar", "sanctions")

STRATEGY_SKILLS = (
    "modern-policy-era-filtering",
    "cornerstone-extraction",
    "triangulation",
    "multilingual-source-handling",
)

REQUIRED_BODY_SECTIONS = ("Knobs available", "Anti-patterns")
ISSUE_318_REQUIRED_SECTIONS = (
    "Official documentation",
    "Auth and cost",
    "Required payload fields",
    "Knobs available",
    "Valid payload examples",
    "Request and pagination pattern",
    "Failure modes",
    "Evidence shape",
    "Anti-patterns",
)


@pytest.fixture(autouse=True)
def _reset_cache() -> None:
    clear_cache()
    yield
    clear_cache()


def _connector_search_params(name: str) -> set[str]:
    module = importlib.import_module(f"research_agent.tools.{name}")
    sig = inspect.signature(module.search)
    return set(sig.parameters)


def _knobs_section_identifiers(body: str) -> set[str]:
    """Extract backtick-wrapped identifiers from the ``## Knobs available`` section.

    A skill's ``## Knobs available`` section uses bullets like
    ``- `kind` — ...``. We collect the first backtick-wrapped token on each
    bullet line so the test can verify those names exist on the connector's
    ``search()`` signature.
    """
    match = re.search(
        r"##\s*Knobs available\s*\n(?P<body>.*?)(?:\n##\s|\Z)",
        body,
        re.DOTALL,
    )
    if not match:
        return set()
    knob_section = match.group("body")
    knobs: set[str] = set()
    for line in knob_section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        m = re.search(r"`([A-Za-z_][A-Za-z0-9_]*)`", stripped)
        if m:
            knobs.add(m.group(1))
    return knobs


def _skill_payload_examples(body: str) -> list[dict[str, object]]:
    examples: list[dict[str, object]] = []
    for match in re.finditer(r"```yaml\s+(?P<body>.*?)```", body, re.DOTALL):
        data = yaml.safe_load(match.group("body"))
        if isinstance(data, dict) and "kind" in data and "payload" in data:
            examples.append(data)
    return examples


@pytest.mark.parametrize("name", CONNECTOR_SKILLS)
def test_connector_skill_loads_with_non_empty_body(name: str) -> None:
    body = load_skill("connectors", name)
    assert body, f"connector skill {name!r} body is empty"
    assert len(body) > 200, f"connector skill {name!r} body looks truncated"


@pytest.mark.parametrize("name", CONNECTOR_SKILLS)
def test_connector_skill_frontmatter_fields_present(name: str) -> None:
    entries = {e["name"]: e for e in list_skills("connectors")}
    assert name in entries, f"skill {name!r} not found in connectors index"
    entry = entries[name]
    assert entry["description"], f"{name}: description missing"
    assert entry["when_to_use"], f"{name}: when_to_use missing"
    assert entry["when_not_to_use"], f"{name}: when_not_to_use missing"


@pytest.mark.parametrize("name", CONNECTOR_SKILLS)
@pytest.mark.parametrize("section", REQUIRED_BODY_SECTIONS)
def test_connector_skill_has_required_section(name: str, section: str) -> None:
    body = load_skill("connectors", name)
    pattern = rf"^##\s+{re.escape(section)}\s*$"
    assert re.search(pattern, body, re.MULTILINE), (
        f"{name}: missing required section '## {section}'"
    )


@pytest.mark.parametrize("name", CONNECTOR_SKILLS)
def test_connector_skill_knobs_match_search_signature(name: str) -> None:
    body = load_skill("connectors", name)
    declared_knobs = _knobs_section_identifiers(body)
    assert declared_knobs, f"{name}: no knobs found in '## Knobs available' section"

    actual_params = _connector_search_params(name)
    unknown = declared_knobs - actual_params
    assert not unknown, (
        f"{name}: knobs {sorted(unknown)} are not parameters of "
        f"research_agent.tools.{name}.search() (actual: {sorted(actual_params)})"
    )


@pytest.mark.parametrize("name", ISSUE_318_CONNECTOR_SKILLS)
def test_issue_318_connector_skill_loads(name: str) -> None:
    body = load_skill("connectors", name)
    assert len(body) > 500
    entries = {entry["name"]: entry for entry in list_skills("connectors")}
    assert entries[name]["description"]
    assert entries[name]["when_to_use"]
    assert entries[name]["when_not_to_use"]


@pytest.mark.parametrize("name", ISSUE_318_CONNECTOR_SKILLS)
@pytest.mark.parametrize("section", ISSUE_318_REQUIRED_SECTIONS)
def test_issue_318_connector_skill_has_required_sections(name: str, section: str) -> None:
    body = load_skill("connectors", name)
    assert re.search(rf"^##\s+{re.escape(section)}\s*$", body, re.MULTILINE)


@pytest.mark.parametrize("name", ISSUE_318_CONNECTOR_SKILLS)
def test_issue_318_connector_skill_examples_validate(name: str) -> None:
    from research_agent.tools._registry import get_kind, validate_payload_contract

    entry = get_kind(f"{name}_search")
    assert entry is not None
    assert entry.skill_name == name

    body = load_skill("connectors", name)
    examples = _skill_payload_examples(body)
    assert examples, f"{name}: expected at least one YAML payload example"
    for example in examples:
        assert example["kind"] == entry.name
        payload = example["payload"]
        assert isinstance(payload, dict)
        result = validate_payload_contract(entry.name, payload)
        assert result.valid, result.repair_message


def test_issue_318_connector_skills_cite_official_docs() -> None:
    expected = {
        "gdelt": "https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/amp/",
        "lda": "https://lda.gov/api/",
        "littlesis": "https://dev.littlesis.org/api/",
        "nonprofits": "https://projects.propublica.org/nonprofits/api/",
        "opencorporates": "https://api.opencorporates.com/documentation/API-Reference",
        "usaspending": "https://api.usaspending.gov/docs/endpoints",
    }
    for name, url in expected.items():
        assert url in load_skill("connectors", name)


@pytest.mark.parametrize("name", ISSUE_319_CONNECTOR_SKILLS)
def test_issue_319_connector_skill_loads(name: str) -> None:
    body = load_skill("connectors", name)
    assert len(body) > 500
    entries = {entry["name"]: entry for entry in list_skills("connectors")}
    assert entries[name]["description"]
    assert entries[name]["when_to_use"]
    assert entries[name]["when_not_to_use"]


@pytest.mark.parametrize("name", ISSUE_319_CONNECTOR_SKILLS)
@pytest.mark.parametrize("section", ISSUE_318_REQUIRED_SECTIONS)
def test_issue_319_connector_skill_has_required_sections(name: str, section: str) -> None:
    body = load_skill("connectors", name)
    assert re.search(rf"^##\s+{re.escape(section)}\s*$", body, re.MULTILINE)


@pytest.mark.parametrize("name", ISSUE_319_CONNECTOR_SKILLS)
def test_issue_319_connector_skill_examples_validate(name: str) -> None:
    from research_agent.tools._registry import get_kind, validate_payload_contract

    entry = get_kind(f"{name}_search")
    assert entry is not None
    assert entry.skill_name == name

    body = load_skill("connectors", name)
    examples = _skill_payload_examples(body)
    assert examples, f"{name}: expected at least one YAML payload example"
    for example in examples:
        assert example["kind"] == entry.name
        payload = example["payload"]
        assert isinstance(payload, dict)
        result = validate_payload_contract(entry.name, payload)
        assert result.valid, result.repair_message


def test_issue_319_connector_skills_cite_official_pages() -> None:
    expected = {
        "bbb": "https://www.bbb.org/all/about-bbb/",
        "calaccess": "https://powersearch.sos.ca.gov/frequently-asked-questions/",
        "licensing": "https://cslb.ca.gov/OnlineServices/CheckLicenseII/CheckLicense.aspx",
    }
    for name, url in expected.items():
        assert url in load_skill("connectors", name)


def test_issue_319_site_navigation_source_boundaries() -> None:
    bbb = load_skill("connectors", "bbb")
    assert "private nonprofit" in bbb
    assert "not a government licensing authority" in bbb

    calaccess = load_skill("connectors", "calaccess")
    assert "Power Search" in calaccess
    assert "Cal-Access" in calaccess
    assert "kind=lobbying" in calaccess
    assert "unsupported" in calaccess

    licensing = load_skill("connectors", "licensing")
    assert "California CSLB" in licensing
    assert "TX" in licensing
    assert "FL" in licensing
    assert "NY" in licensing
    assert "stubs" in licensing
    assert "unsupported" in licensing


@pytest.mark.parametrize("name", ISSUE_320_CONNECTOR_SKILLS)
def test_issue_320_connector_skill_loads(name: str) -> None:
    body = load_skill("connectors", name)
    assert len(body) > 500
    entries = {entry["name"]: entry for entry in list_skills("connectors")}
    assert entries[name]["description"]
    assert entries[name]["when_to_use"]
    assert entries[name]["when_not_to_use"]


@pytest.mark.parametrize("name", ISSUE_320_CONNECTOR_SKILLS)
@pytest.mark.parametrize("section", ISSUE_318_REQUIRED_SECTIONS)
def test_issue_320_connector_skill_has_required_sections(name: str, section: str) -> None:
    body = load_skill("connectors", name)
    assert re.search(rf"^##\s+{re.escape(section)}\s*$", body, re.MULTILINE)


@pytest.mark.parametrize("name", ISSUE_320_CONNECTOR_SKILLS)
def test_issue_320_connector_skill_examples_validate(name: str) -> None:
    from research_agent.tools._registry import get_kind, validate_payload_contract

    entry = get_kind(f"{name}_search")
    assert entry is not None
    assert entry.skill_name == name

    body = load_skill("connectors", name)
    examples = _skill_payload_examples(body)
    assert examples, f"{name}: expected at least one YAML payload example"
    for example in examples:
        assert example["kind"] == entry.name
        payload = example["payload"]
        assert isinstance(payload, dict)
        result = validate_payload_contract(entry.name, payload)
        assert result.valid, result.repair_message


def test_issue_320_connector_skills_cite_current_official_docs() -> None:
    expected = {
        "linkedin": (
            "https://nubela.co/proxycurl/auth/register.html",
            "https://nubela.co/blog/what-is-proxycurl-api-now-in-2026-im-the-founder/",
            "https://lix-it.com/docs/",
            "https://lix-it.com/pages/linkedin-api",
        ),
        "scholar": (
            "https://serpapi.com/google-scholar-api",
            "https://serpapi.com/pricing",
        ),
        "sanctions": (
            "https://ofac.treasury.gov/sanctions-list-service",
            "https://finance.ec.europa.eu/eu-and-world/sanctions-restrictive-measures/overview-sanctions-and-related-resources_en",
            "https://www.gov.uk/government/publications/the-uk-sanctions-list",
            "https://sanctionssearchapp.ofsi.hmtreasury.gov.uk/",
        ),
    }
    for name, urls in expected.items():
        body = load_skill("connectors", name)
        for url in urls:
            assert url in body


def test_issue_320_paid_and_sanctions_caveats_are_explicit() -> None:
    linkedin = load_skill("connectors", "linkedin")
    assert "Proxycurl is no longer in service" in linkedin
    assert "NinjaPear is not a drop-in replacement implemented here" in linkedin
    assert "paid/gated" in linkedin

    scholar = load_skill("connectors", "scholar")
    assert "SERPAPI_KEY" in scholar
    assert "openalex_search" in scholar
    assert "no_cache" in scholar

    sanctions = load_skill("connectors", "sanctions")
    assert "UK Sanctions List is now the authoritative source" in sanctions
    assert "OFSI Consolidated List" in sanctions
    assert "2026-01-28" in sanctions
    assert "EU rows as stale" in sanctions


def test_issue_320_payload_contract_rejects_invalid_modes() -> None:
    from research_agent.tools._registry import validate_payload_contract

    linkedin_result = validate_payload_contract(
        "linkedin_search",
        {
            "query": "Jane Doe",
            "sub_question": "Find a LinkedIn lead",
            "kind": "profile",
        },
    )
    assert linkedin_result.valid is False
    assert "kind" in linkedin_result.repair_message

    scholar_result = validate_payload_contract(
        "scholar_search",
        {
            "query": "Section 230",
            "sub_question": "Find case law",
            "kind": "cases",
        },
    )
    assert scholar_result.valid is False
    assert "kind" in scholar_result.repair_message

    sanctions_result = validate_payload_contract(
        "sanctions_search",
        {
            "query": "Wagner Group",
            "sub_question": "Screen sanctions",
            "kinds": ["OFSI"],
        },
    )
    assert sanctions_result.valid is False
    assert "kinds" in sanctions_result.repair_message


def test_congress_skill_carries_canonical_motivator() -> None:
    """The 110th-Congress / IRA relevance trap is the headline reason this
    skill exists; the body must keep that example intact."""
    body = load_skill("connectors", "congress")
    assert "117" in body
    assert "119" in body
    assert "Inflation Reduction Act" in body


def test_skill_descriptions_are_one_line() -> None:
    """The description is the planner-facing index signal — must stay terse
    and single-line so it stays cheap to render across all 18 connectors."""
    for entry in list_skills("connectors"):
        assert "\n" not in entry["description"], (
            f"{entry['name']}: description must be a single line"
        )
        assert len(entry["description"]) <= 280, (
            f"{entry['name']}: description longer than 280 chars "
            f"({len(entry['description'])})"
        )


def test_loader_module_resolves_skills_directory(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sanity: skill files live where the loader expects (no install/path drift)."""
    base = skills_loader._skills_dir("connectors")
    assert base.is_dir(), f"connectors directory missing at {base}"
    shipped = sorted(p.stem for p in base.glob("*.md"))
    for name in CONNECTOR_SKILLS:
        assert name in shipped, f"{name}.md missing from {base}"


# ---------------------------------------------------------------------------
# Strategy skills
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", STRATEGY_SKILLS)
def test_strategy_skill_loads_with_non_empty_body(name: str) -> None:
    body = load_skill("strategies", name)
    assert body, f"strategy skill {name!r} body is empty"
    assert len(body) > 200, f"strategy skill {name!r} body looks truncated"


@pytest.mark.parametrize("name", STRATEGY_SKILLS)
def test_strategy_skill_frontmatter_fields_present(name: str) -> None:
    entries = {e["name"]: e for e in list_skills("strategies")}
    assert name in entries, f"skill {name!r} not found in strategies index"
    entry = entries[name]
    assert entry["description"], f"{name}: description missing"
    assert entry["when_to_use"], f"{name}: when_to_use missing"


def test_strategy_descriptions_are_one_line() -> None:
    """The description is the planner-facing index signal — single-line, terse."""
    for entry in list_skills("strategies"):
        assert "\n" not in entry["description"], (
            f"{entry['name']}: description must be a single line"
        )
        assert len(entry["description"]) <= 280, (
            f"{entry['name']}: description longer than 280 chars "
            f"({len(entry['description'])})"
        )


def test_modern_policy_era_filtering_references_every_connector() -> None:
    """The strategy's value prop is "stack onto every connector" — its body
    must concretely name each shipped connector and reference the one real
    date knob (`since` on fedregister), so the planner gets actionable
    guidance instead of generic principles."""
    body = load_skill("strategies", "modern-policy-era-filtering")
    for connector in CONNECTOR_SKILLS:
        assert connector in body, (
            f"modern-policy-era-filtering: body must reference connector "
            f"{connector!r} so planner gets per-connector directive"
        )
    assert "since" in body, (
        "modern-policy-era-filtering: must reference the `since` knob "
        "(the one real date parameter on fedregister.search())"
    )
    assert "2025-01-20" in body, (
        "modern-policy-era-filtering: must reference the 119th-Congress / "
        "Trump-2-inauguration anchor date"
    )


def test_strategies_directory_resolves() -> None:
    """Sanity: strategy files live where the loader expects."""
    base = skills_loader._skills_dir("strategies")
    assert base.is_dir(), f"strategies directory missing at {base}"
    shipped = sorted(p.stem for p in base.glob("*.md"))
    for name in STRATEGY_SKILLS:
        assert name in shipped, f"{name}.md missing from {base}"
