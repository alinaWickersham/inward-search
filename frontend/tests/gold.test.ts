import { describe, expect, it, vi } from "vitest";

import { ApiError, type FetchFn, requestJson } from "../src/api.js";
import { addQuery, deleteQuery, parseGoldQuery, saveQuery } from "../src/gold.js";
import { jsonResponse } from "./fixtures.js";
import { goldQuery } from "./labelFixtures.js";

describe("parseGoldQuery", () => {
  it("accepts a well-formed query", () => {
    const query = goldQuery({ pool: ["L1"], judgements: { L1: 1 }, triage: "seeking" });
    expect(parseGoldQuery(structuredClone(query))).toEqual(query);
  });

  it.each([
    ["intent missing", { ...goldQuery(), intent: undefined }, "query is malformed"],
    ["a dimension missing", { ...goldQuery(), intent: { social: [] } }, "intent.structure is malformed"],
    ["pool not a list of ids", { ...goldQuery(), pool: [1] }, "pool is malformed"],
    ["a grade of 2", { ...goldQuery(), pool: ["L1"], judgements: { L1: 2 } }, "a judgement is not 0 or 1"],
    ["triage not a string", { ...goldQuery(), triage: 3 }, "triage is not a string"],
  ])("rejects a query with %s", (_, body, message) => {
    expect(() => parseGoldQuery(body)).toThrow(new ApiError(`Unexpected response: ${message}`));
  });
});

describe("requests", () => {
  it("saves with PUT to the query's URL and returns the server's copy", async () => {
    const query = goldQuery({ triage: "seeking" });
    const fetchFn = vi.fn<FetchFn>(async () => jsonResponse(query));
    await expect(saveQuery(fetchFn, query)).resolves.toEqual(query);
    const [url, init] = fetchFn.mock.calls[0];
    expect([url, init.method, JSON.parse(init.body as string)]).toEqual(["/api/gold/Q001", "PUT", query]);
  });

  it("adds with POST and the text as JSON", async () => {
    const fetchFn = vi.fn<FetchFn>(async () => jsonResponse(goldQuery({ id: "Q002" }), 201));
    await addQuery(fetchFn, "a quiet week");
    expect(JSON.parse(fetchFn.mock.calls[0][1].body as string)).toEqual({ text: "a quiet week" });
  });

  it("treats a 204 as success with no body", async () => {
    const fetchFn: FetchFn = async () => new Response(null, { status: 204 });
    await expect(deleteQuery(fetchFn, "Q001")).resolves.toBeUndefined();
    await expect(requestJson(fetchFn, "/x", {}, "Deleting")).resolves.toBeNull();
  });

  it("names the action that failed", async () => {
    const fetchFn: FetchFn = async () => jsonResponse({ detail: "the pool changed; reload the query" }, 409);
    await expect(saveQuery(fetchFn, goldQuery())).rejects.toThrow(
      new ApiError("Saving failed: the pool changed; reload the query."),
    );
  });
});
