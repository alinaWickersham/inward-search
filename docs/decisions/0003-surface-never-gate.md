# 0003. Triage surfaces resources and never gates results

Date: 2026-09-07
Status: accepted

## Context

The same sentence, "I have been running on empty and need to get away from
everything", is sometimes spiritual seeking and sometimes something a
retreat will not help with. The system has to do something with that
ambiguity. The obvious product instinct is to filter: withhold intensive
retreats from people whose queries suggest they are struggling.

## Decision

Triage classifies the query into one of four routing classes and changes
only what the response *adds*: nothing for seeking, a weighting hint for
stress, a clearly separated note with support resources for possible
clinical need, and resources placed first for acute risk. Results are
never removed, reordered, or withheld on the basis of the classification.
The classification is never stored, logged, or traced. No output names or
implies a condition or uses assessment language.

## Alternatives considered

**Filter or block results for high-need classes.** This is a clinical
judgment made by a system not qualified to make it, on a sentence, about a
person it cannot see. It also creates a duty of care the system cannot
discharge, and it is the design most likely to be wrong in the cases that
matter: a person turned away learns nothing and goes elsewhere.

**No triage at all.** Every existing product does this. It is the failure
the project exists to address.

**Triage as a gate with an override.** Softer, but the gate still makes the
judgment; the override only shifts the burden to the person.

## Consequences

The person keeps their choice in every case, and the system's only failure
mode is offering a resource that was not needed, which is cheap. The hard
constraint this places on every later module is that no code path may read
the triage class to alter the result list, and observability must exclude
it explicitly. The evaluation reports false negatives on the two
highest-need classes separately, because a missed offer is the failure that
matters.
