// Pure updates to a gold query. The page calls these, then saves the result.

import type { DimensionKey } from "./api.js";
import type { GoldQuery, Grade } from "./gold.js";

export function toggleIntentValue(query: GoldQuery, key: DimensionKey, value: string): GoldQuery {
  const current = query.intent[key];
  const next = current.includes(value)
    ? current.filter((item) => item !== value)
    : [...current, value];
  return { ...query, intent: { ...query.intent, [key]: next } };
}

export function setTriage(query: GoldQuery, triage: string | null): GoldQuery {
  return { ...query, triage };
}

export function judge(query: GoldQuery, listingId: string, grade: Grade): GoldQuery {
  if (!query.pool.includes(listingId)) throw new Error(`${listingId} is not in the pool`);
  return { ...query, judgements: { ...query.judgements, [listingId]: grade } };
}

/**
 * Index of the first unjudged pool listing after `from`, wrapping round to
 * the start. -1 when everything is judged.
 */
export function nextUnjudged(query: GoldQuery, from: number): number {
  const size = query.pool.length;
  for (let step = 1; step <= size; step++) {
    const index = (from + step + size) % size;
    if (!(query.pool[index] in query.judgements)) return index;
  }
  return -1;
}

/** Mirrors GoldQuery.complete in Python. */
export function isComplete(query: GoldQuery): boolean {
  return (
    query.triage !== null &&
    query.pool.length > 0 &&
    query.pool.every((id) => id in query.judgements)
  );
}
