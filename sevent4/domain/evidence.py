from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

SOURCE_PROFILE_RE = re.compile(r"^[a-z]{2}-[a-z0-9]+-[a-z0-9]+(?:-[a-z0-9]+)*$")
CLAIM_ID_ATTR_RE = re.compile(r"""data-claim-id=["']([^"']+)["']""")

VALID_TRANSPORTS = {
    "direct-http",
    "browser-rendered",
    "google-drive-download",
    "india-fetch-box-socks",
    "manual-rti-upload",
}
VALID_SOURCE_ROLES = {
    "official_record",
    "court_record",
    "legislative_record",
    "secondary_research",
    "news_corroboration",
}
VALID_FACT_STATUS = {"found", "partial", "not_found"}
VALID_CONFIDENCE = {"high", "medium", "low"}


@dataclass(frozen=True)
class SourceProfile:
    id: str
    country: str
    institution: str
    source_family: str
    transport: str
    source_role: str
    owner_repo: str
    retrieval_date: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceProfile":
        profile = cls(
            id=_required_str(data, "id"),
            country=_required_str(data, "country"),
            institution=_required_str(data, "institution"),
            source_family=_required_str(data, "source_family"),
            transport=_required_str(data, "transport"),
            source_role=_required_str(data, "source_role"),
            owner_repo=_required_str(data, "owner_repo"),
            retrieval_date=_optional_str(data, "retrieval_date"),
        )
        profile.validate()
        return profile

    def validate(self) -> None:
        _reject_implementation_name(self.id, "source profile id")
        if not SOURCE_PROFILE_RE.fullmatch(self.id):
            raise ValueError(f"{self.id}: source profile id must be kebab-case")
        if self.transport not in VALID_TRANSPORTS:
            raise ValueError(f"{self.id}: invalid transport {self.transport}")
        if self.source_role not in VALID_SOURCE_ROLES:
            raise ValueError(f"{self.id}: invalid source_role {self.source_role}")
        if self.owner_repo not in {"commoner-probe", "partial-recall", "public-finance", "sevent4"}:
            raise ValueError(f"{self.id}: invalid owner_repo {self.owner_repo}")


@dataclass(frozen=True)
class FactRecord:
    id: str
    kind: str
    metric: str
    value: Any
    unit: str
    period: str
    source_id: str
    source_locator: str
    extractor: str
    confidence: str
    status: str
    geography: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FactRecord":
        fact = cls(
            id=_required_str(data, "id"),
            kind=_required_str(data, "kind"),
            metric=_required_str(data, "metric"),
            value=data.get("value"),
            unit=_required_str(data, "unit"),
            period=_required_str(data, "period"),
            source_id=_required_str(data, "source_id"),
            source_locator=_required_str(data, "source_locator"),
            extractor=_required_str(data, "extractor"),
            confidence=_required_str(data, "confidence"),
            status=_required_str(data, "status"),
            geography=_required_dict(data, "geography"),
        )
        fact.validate()
        return fact

    def validate(self) -> None:
        if self.confidence not in VALID_CONFIDENCE:
            raise ValueError(f"{self.id}: invalid confidence {self.confidence}")
        if self.status not in VALID_FACT_STATUS:
            raise ValueError(f"{self.id}: invalid status {self.status}")
        if self.status == "not_found" and self.value is not None:
            raise ValueError(f"{self.id}: not_found facts must use null value")
        if self.status == "found" and self.value is None:
            raise ValueError(f"{self.id}: found facts must carry a value")
        if not self.geography.get("country"):
            raise ValueError(f"{self.id}: geography.country is required")
        _reject_implementation_name(self.extractor, "extractor")


@dataclass(frozen=True)
class ClaimRecord:
    id: str
    text: str
    fact_ids: tuple[str, ...]
    public_route: str
    constitutional_relevance: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClaimRecord":
        claim = cls(
            id=_required_str(data, "id"),
            text=_required_str(data, "text"),
            fact_ids=tuple(_required_list(data, "fact_ids")),
            public_route=_required_str(data, "public_route"),
            constitutional_relevance=_required_dict(data, "constitutional_relevance"),
        )
        claim.validate()
        return claim

    def validate(self) -> None:
        if not self.fact_ids:
            raise ValueError(f"{self.id}: claim must reference at least one fact")
        if not self.public_route.startswith("/"):
            raise ValueError(f"{self.id}: public_route must be an absolute route")
        if not self.constitutional_relevance.get("twelfth_schedule_function"):
            raise ValueError(f"{self.id}: missing Twelfth Schedule function")


@dataclass(frozen=True)
class EvidenceBundle:
    schema: str
    source_profiles: tuple[SourceProfile, ...]
    facts: tuple[FactRecord, ...]
    claims: tuple[ClaimRecord, ...]

    def claim_by_id(self, claim_id: str) -> ClaimRecord:
        for claim in self.claims:
            if claim.id == claim_id:
                return claim
        raise KeyError(claim_id)

    def validate(self) -> None:
        source_ids = {profile.id for profile in self.source_profiles}
        for fact in self.facts:
            if fact.source_id not in source_ids:
                raise ValueError(f"{fact.id}: references unknown source {fact.source_id}")
        validate_claims_against_facts(list(self.claims), list(self.facts))


def evidence_bundle_from_dict(data: dict[str, Any]) -> EvidenceBundle:
    bundle = EvidenceBundle(
        schema=_required_str(data, "schema"),
        source_profiles=tuple(SourceProfile.from_dict(row) for row in data.get("source_profiles", [])),
        facts=tuple(FactRecord.from_dict(row) for row in data.get("facts", [])),
        claims=tuple(ClaimRecord.from_dict(row) for row in data.get("claims", [])),
    )
    bundle.validate()
    return bundle


def claim_ids_in_html(html: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(claim_id for claim_id in CLAIM_ID_ATTR_RE.findall(html) if "${" not in claim_id))


def validate_claims_against_facts(claims: list[ClaimRecord], facts: list[FactRecord]) -> None:
    fact_ids = {fact.id for fact in facts}
    for claim in claims:
        missing = [fact_id for fact_id in claim.fact_ids if fact_id not in fact_ids]
        if missing:
            raise ValueError(f"{claim.id}: references unknown facts: {', '.join(missing)}")


def validate_claim_ids(claim_ids: tuple[str, ...], bundle: EvidenceBundle, label: str) -> None:
    bundle_claim_ids = {claim.id for claim in bundle.claims}
    missing = [claim_id for claim_id in claim_ids if claim_id not in bundle_claim_ids]
    if missing:
        raise ValueError(f"{label} references unknown claims: {', '.join(missing)}")


def _required_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


def _optional_str(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a string when provided")
    return value


def _required_dict(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{key} is required")
    return value


def _required_list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{key} must be a non-empty list of strings")
    return value


def _reject_implementation_name(value: str, label: str) -> None:
    if any(char.isupper() for char in value) or "fetcher" in value.lower():
        raise ValueError(f"{label} must name the source contract, not an implementation class")

