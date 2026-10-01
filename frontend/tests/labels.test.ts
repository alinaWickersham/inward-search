import { describe, expect, it } from "vitest";

import { DIMENSION_KEYS } from "../src/api.js";
import { DIMENSION_LABELS, valueLabel } from "../src/labels.js";

describe("labels", () => {
  it("names every dimension", () => {
    expect(Object.keys(DIMENSION_LABELS).sort()).toEqual([...DIMENSION_KEYS].sort());
  });

  it("turns a schema value into reader text", () => {
    expect(valueLabel("buddhist_derived")).toBe("Buddhist-derived");
    expect(valueLabel("free_or_donation")).toBe("free or donation");
  });

  it("shows an unknown value as sent rather than dropping it", () => {
    expect(valueLabel("not_in_the_table")).toBe("not_in_the_table");
  });
});
