import { describe, expect, it } from "vitest";

import {
  isComplete,
  judge,
  nextUnjudged,
  setTriage,
  toggleIntentValue,
} from "../src/labelState.js";
import { goldQuery } from "./labelFixtures.js";

describe("toggleIntentValue", () => {
  it("adds a value, adds a second, then removes the first", () => {
    let query = toggleIntentValue(goldQuery(), "duration", "weekend");
    query = toggleIntentValue(query, "duration", "week");
    expect(query.intent.duration).toEqual(["weekend", "week"]);
    query = toggleIntentValue(query, "duration", "weekend");
    expect(query.intent.duration).toEqual(["week"]);
  });

  it("does not modify the query it was given", () => {
    const original = goldQuery();
    toggleIntentValue(original, "speech", "full_silence");
    expect(original.intent.speech).toEqual([]);
  });
});

describe("judge", () => {
  it("records a grade for a pool listing and can overwrite it", () => {
    const query = goldQuery({ pool: ["L1", "L2"] });
    expect(judge(judge(query, "L1", 1), "L1", 0).judgements).toEqual({ L1: 0 });
  });

  it("refuses a listing outside the pool", () => {
    expect(() => judge(goldQuery({ pool: ["L1"] }), "L9", 1)).toThrow("L9 is not in the pool");
  });
});

describe("nextUnjudged", () => {
  const query = goldQuery({ pool: ["L1", "L2", "L3", "L4"], judgements: { L1: 1, L3: 0 } });

  it.each([
    [-1, 1],
    [1, 3],
    [3, 1],
  ])("from index %i goes to %i, wrapping round", (from, expected) => {
    expect(nextUnjudged(query, from)).toBe(expected);
  });

  it("is -1 when everything is judged", () => {
    expect(nextUnjudged(goldQuery({ pool: ["L1"], judgements: { L1: 0 } }), 0)).toBe(-1);
  });
});

describe("isComplete", () => {
  const judged = goldQuery({ pool: ["L1"], judgements: { L1: 1 } });

  it("needs a triage class, a pool, and every judgement", () => {
    expect(isComplete(setTriage(judged, "seeking"))).toBe(true);
    expect(isComplete(judged)).toBe(false);
    expect(isComplete(goldQuery({ triage: "seeking" }))).toBe(false);
    expect(isComplete(goldQuery({ triage: "seeking", pool: ["L1", "L2"], judgements: { L1: 1 } }))).toBe(false);
  });
});
