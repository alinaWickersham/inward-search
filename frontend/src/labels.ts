// Display text for the intent dimensions, matching the README table.
// tests/api/test_frontend_labels.py fails if a schema value is missing here.

import type { DimensionKey } from "./api.js";

export const DIMENSION_LABELS: Record<DimensionKey, string> = {
  social: "Social",
  structure: "Structure",
  speech: "Speech",
  guidance: "Guidance",
  physical_demand: "Physical demand",
  tradition: "Tradition",
  experience_level: "Experience level",
  duration: "Duration",
  cost_band: "Cost band",
};

export const VALUE_LABELS: Record<string, string> = {
  solitude: "solitude",
  small_group: "small group",
  community: "community",
  fixed: "fixed",
  semi_structured: "semi-structured",
  self_directed: "self-directed",
  full_silence: "full silence",
  partial_silence: "partial silence",
  dialogue: "dialogue",
  teacher_led: "teacher-led",
  light_guidance: "light guidance",
  self_guided: "self-guided",
  restful: "restful",
  moderate: "moderate",
  demanding: "demanding",
  secular: "secular",
  buddhist_derived: "Buddhist-derived",
  yogic: "yogic",
  contemplative_christian: "contemplative Christian",
  nature_based: "nature-based",
  eclectic: "eclectic",
  newcomer_friendly: "newcomer-friendly",
  some_experience: "some experience",
  assumes_practice: "assumes practice",
  hours: "hours",
  weekend: "weekend",
  week: "week",
  extended: "extended",
  free_or_donation: "free or donation",
  low: "low",
  mid: "mid",
  high: "high",
};

/** A value the table does not know is shown as sent rather than hidden. */
export function valueLabel(value: string): string {
  return VALUE_LABELS[value] ?? value;
}

/** The values each dimension can take, in schema order. */
export const DIMENSION_VALUES: Record<DimensionKey, string[]> = {
  social: ["solitude", "small_group", "community"],
  structure: ["fixed", "semi_structured", "self_directed"],
  speech: ["full_silence", "partial_silence", "dialogue"],
  guidance: ["teacher_led", "light_guidance", "self_guided"],
  physical_demand: ["restful", "moderate", "demanding"],
  tradition: [
    "secular",
    "buddhist_derived",
    "yogic",
    "contemplative_christian",
    "nature_based",
    "eclectic",
  ],
  experience_level: ["newcomer_friendly", "some_experience", "assumes_practice"],
  duration: ["hours", "weekend", "week", "extended"],
  cost_band: ["free_or_donation", "low", "mid", "high"],
};

// Triage classes are routing classes: they decide which resources a response
// offers alongside its results. They never describe the person.
export const TRIAGE_LABELS: Record<string, string> = {
  seeking: "Seeking",
  stress_burnout: "Stress or burnout",
  possible_clinical_need: "Possible clinical need (routing class)",
  acute_risk: "Acute risk",
};
