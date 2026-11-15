"""Public contracts. Missing scores stay None; imputation happens only in totals."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

DemandType = Literal["professional_resources", "issue_collaboration", "volunteering", "resource_support"]
Dimension = Literal["resource_need", "semantic", "readiness", "time", "size", "issue", "target", "area", "membership", "participation"]
State = Literal["Known", "Unknown", "Not Required"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Period(Contract):
    start: date
    end: date

    @model_validator(mode="after")
    def check_order(self):
        if self.end < self.start:
            raise ValueError("period.end must be on or after period.start")
        return self


class Demand(Contract):
    description: str = Field(min_length=1, max_length=6000)
    demand_type: DemandType | None = None
    # Resource keys are validated by build_plan, which also returns the rule catalog.
    resources: list[str] = Field(default_factory=list, max_length=10)
    resource_mode: Literal["any", "all"] = "any"
    custom_resource_terms: list[str] = Field(default_factory=list, max_length=10)
    resource_direction: Literal["offer_to_ngo", "seek_ngo_service"] = "offer_to_ngo"
    plan_name: str | None = Field(default=None, min_length=2, max_length=120)
    issues: list[str] = Field(default_factory=list, max_length=20)
    target_groups: list[str] = Field(default_factory=list, max_length=20)
    areas: list[str] = Field(default_factory=list, max_length=30)
    area_basis: Literal["service_area", "registered_area"] = "service_area"
    staff_min: int | None = Field(default=None, ge=0)
    staff_max: int | None = Field(default=None, ge=0)
    memberships: list[str] = Field(default_factory=list, max_length=10)
    period: Period | None = None
    required_conditions: list[Dimension] = Field(default_factory=list)
    # Keep corporate reporting purposes out of semantic retrieval and NGO requirements.
    corporate_purpose: str | None = Field(default=None, max_length=2000)
    target_count: int = Field(default=10, ge=1, le=200)
    candidate_limit: int | None = Field(default=None, ge=1, le=500)

    @model_validator(mode="after")
    def check_values(self):
        if self.staff_min is not None and self.staff_max is not None and self.staff_min > self.staff_max:
            raise ValueError("staff_min must not exceed staff_max")
        for name in ("resources", "custom_resource_terms", "issues", "target_groups", "areas", "memberships"):
            values = getattr(self, name)
            if any(not value.strip() for value in values):
                raise ValueError(f"{name} cannot contain blank values")
            setattr(self, name, list(dict.fromkeys(values)))
        if self.candidate_limit is not None and self.candidate_limit < self.target_count:
            raise ValueError("candidate_limit must be at least target_count")
        return self


class Plan(Contract):
    demand_type: DemandType | None
    weights: dict[str, float]
    inactive_dimensions: list[str]
    clarification_questions: list[str]
    warnings: list[str]
    candidate_limit: int


class Evidence(Contract):
    evidence_id: str
    npo_id: str
    source_sheet: str
    source_record_id: str
    source_url: str
    row: int
    event_date: date | None = None
    event_name: str = ""
    source_kind: Literal["profile", "contact_record", "consultant_note"]
    quote: str
    original_text: str
    start: int = 0
    end: int = 0


class Organization(Contract):
    npo_id: str
    name: str
    profile: dict[str, str]
    evidence: list[Evidence] = Field(default_factory=list)


class Snapshot(Contract):
    captured_at: str
    organizations: list[Organization]
    warnings: list[str] = Field(default_factory=list)


class Subscore(Contract):
    state: State
    score: float | None = Field(default=None, ge=0, le=100)
    reason: str
    evidence_ids: list[str] = Field(default_factory=list)
    raw_cosine: float | None = Field(default=None, ge=-1, le=1)
    method: Literal["rule", "bge", "rule_override"] = "rule"
    evidence_trust: float | None = Field(default=None, ge=0, le=1)
    evidence_age_days: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def check_state(self):
        if (self.state == "Known") != (self.score is not None):
            raise ValueError("Only Known subscores must contain a score")
        return self


class EligibilityCheck(Contract):
    status: Literal["Eligible", "Ineligible", "Unverified"]
    reason: str
    evidence_ids: list[str] = Field(default_factory=list)


class Recommendation(Contract):
    npo_id: str
    npo_name: str
    match_score: float
    known_score: float | None
    score_range: tuple[float, float]
    subscores: dict[str, Subscore]
    evidence_coverage: float
    evidence_trust: float = Field(default=0, ge=0, le=1)
    trusted_evidence_coverage: float = Field(default=0, ge=0, le=1)
    ranking_score: float = Field(default=0, ge=0, le=100)
    verification_required: bool = True
    scoring_status: Literal["review_candidate", "historical_candidate", "semantic_candidate", "needs_verification", "insufficient_evidence", "core_mismatch", "ineligible"]
    eligibility_status: Literal["Eligible", "Ineligible", "Unverified"]
    eligibility_checks: dict[str, EligibilityCheck]
    weights_used: dict[str, float]
    recommendation_reasons: list[str]
    source_evidence: list[Evidence]
    warnings: list[str]
    missing_information: list[str]
    scoring_version: str
    calibration_status: str = "uncalibrated"
    data_snapshot_at: str


class RecommendationResponse(Contract):
    status: Literal["success", "needs_clarification"]
    plan: Plan
    recommendations: list[Recommendation] = Field(default_factory=list)
    excluded: list[Recommendation] = Field(default_factory=list)
    total_organizations: int = 0
    available_candidates: int = 0
    warnings: list[str] = Field(default_factory=list)
