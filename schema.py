"""
Core schema for Threshold.

The intent dimensions are the heart of the project: a listing is annotated
on them, a query is parsed into a partial specification over them, and
retrieval matches the two. Get these right before generating 120 listings
against them, because changing a dimension later means re-annotating
everything.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# --------------------------------------------------------------------------
# Dimensions
# --------------------------------------------------------------------------

class Social(str, Enum):
    SOLITUDE = "solitude"              # alone, minimal contact
    SMALL_GROUP = "small_group"        # under ~15, some shared life
    COMMUNITY = "community"            # larger, communal


class Structure(str, Enum):
    FIXED = "fixed"                    # published schedule, expected attendance
    SEMI = "semi_structured"           # anchor sessions, free time between
    SELF_DIRECTED = "self_directed"    # you decide your days


class Speech(str, Enum):
    FULL_SILENCE = "full_silence"
    PARTIAL_SILENCE = "partial_silence"   # silent periods, e.g. mornings or meals
    DIALOGUE = "dialogue"                 # conversation is part of the point


class Guidance(str, Enum):
    TEACHER_LED = "teacher_led"
    LIGHT = "light_guidance"           # available, not constant
    SELF_GUIDED = "self_guided"


class PhysicalDemand(str, Enum):
    RESTFUL = "restful"
    MODERATE = "moderate"
    DEMANDING = "demanding"            # long sits, long hikes, early starts


class Tradition(str, Enum):
    SECULAR = "secular"
    BUDDHIST = "buddhist_derived"
    YOGIC = "yogic"
    CHRISTIAN = "contemplative_christian"
    NATURE = "nature_based"
    ECLECTIC = "eclectic"


class ExperienceLevel(str, Enum):
    NEWCOMER = "newcomer_friendly"
    SOME = "some_experience"
    EXPERIENCED = "assumes_practice"


class Duration(str, Enum):
    HOURS = "hours"
    WEEKEND = "weekend"
    WEEK = "week"
    EXTENDED = "extended"              # longer than a week


class CostBand(str, Enum):
    FREE = "free_or_donation"
    LOW = "low"
    MID = "mid"
    HIGH = "high"


# --------------------------------------------------------------------------
# Listing
# --------------------------------------------------------------------------

class ListingDimensions(BaseModel):
    """How a listing sits on each dimension. All required — every listing
    gets a value on every axis, so retrieval never has to handle nulls."""
    social: Social
    structure: Structure
    speech: Speech
    guidance: Guidance
    physical_demand: PhysicalDemand
    tradition: Tradition
    experience_level: ExperienceLevel
    duration: Duration
    cost_band: CostBand


class Listing(BaseModel):
    id: str
    name: str
    location: str                      # invented place, region-level realism
    summary: str = Field(description="One or two sentences, as a directory would show")
    description: str = Field(description="The listing body, 150-350 words, in the operator's own voice")
    practical: str = Field(description="Dates, what's included, what to bring — as listings actually write it")
    dimensions: ListingDimensions

    # Populated in weekend 6, left empty for now.
    trust_notes: Optional[str] = None
    contraindication_notes: Optional[str] = None

    synthetic: bool = True             # never remove this


# --------------------------------------------------------------------------
# Query intent
# --------------------------------------------------------------------------

class QueryIntent(BaseModel):
    """A parsed query. Every field optional — most people constrain three
    or four dimensions, not nine. Absence means 'no preference', which is
    different from a middle value."""
    social: Optional[Social] = None
    structure: Optional[Structure] = None
    speech: Optional[Speech] = None
    guidance: Optional[Guidance] = None
    physical_demand: Optional[PhysicalDemand] = None
    tradition: Optional[Tradition] = None
    experience_level: Optional[ExperienceLevel] = None
    duration: Optional[Duration] = None
    cost_band: Optional[CostBand] = None

    reasoning: Optional[str] = Field(
        default=None,
        description="Why these dimensions were inferred — used for the explanation shown to the user",
    )


# --------------------------------------------------------------------------
# Triage (weekend 5 — defined here so the schema stays in one place)
# --------------------------------------------------------------------------

class TriageClass(str, Enum):
    SEEKING = "seeking"
    STRESS = "stress_burnout"
    POSSIBLE_CLINICAL = "possible_clinical_need"
    ACUTE = "acute_risk"
