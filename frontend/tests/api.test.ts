import { describe, expect, it, vi } from "vitest";

import { parseSearchResponse, search, SEARCH_URL, SearchError, searchRequest } from "../src/api.js";
import { jsonResponse, listing, response, result } from "./fixtures.js";

describe("searchRequest", () => {
  it("posts the query and k as JSON, keeping the text out of the URL", () => {
    const init = searchRequest('quiet & "calm"?', 10);
    expect(init.method).toBe("POST");
    expect(init.headers).toEqual({ "Content-Type": "application/json" });
    expect(JSON.parse(init.body as string)).toEqual({ query: 'quiet & "calm"?', k: 10 });
  });
});

describe("parseSearchResponse", () => {
  it("accepts a well-formed response unchanged", () => {
    const body = response([result(1, 0.9), result(2, 0.5, listing({ id: "L002" }))]);
    expect(parseSearchResponse(structuredClone(body))).toEqual(body);
  });

  it.each([
    ["not an object", null, "results are missing"],
    ["results not an array", { ...response([]), results: {} }, "results are missing"],
    ["model missing", { query: "q", strategy: "embedding", results: [] }, "model is not a string"],
    ["result not an object", response([1 as never]), "results[0] is malformed"],
    ["score not a number", response([result(1, "0.9" as never)]), "results[0].score is not a number"],
    [
      "listing without dimensions",
      response([{ rank: 1, score: 1, listing: { id: "L001" } as never }]),
      "results[0].listing is malformed",
    ],
    [
      "dimension missing",
      response([result(1, 1, { ...listing(), dimensions: { social: "solitude" } as never })]),
      "results[0].listing.dimensions.structure is not a string",
    ],
    [
      "synthetic not a boolean",
      response([result(1, 1, listing({ synthetic: "yes" as never }))]),
      "results[0].listing.synthetic is not a boolean",
    ],
  ])("rejects a response with %s", (_, body, message) => {
    expect(() => parseSearchResponse(body)).toThrow(new SearchError(`Unexpected response: ${message}`));
  });
});

describe("search", () => {
  it("requests the search URL and returns the parsed body", async () => {
    const body = response([result(1, 0.75)]);
    const fetchFn = vi.fn(async () => jsonResponse(body));
    await expect(search("somewhere quiet", 5, fetchFn)).resolves.toEqual(body);
    expect(fetchFn).toHaveBeenCalledWith(SEARCH_URL, searchRequest("somewhere quiet", 5));
  });

  it("shows the server's message when it gives one", async () => {
    const fetchFn = async () => jsonResponse({ detail: "query is empty" }, 422);
    await expect(search("x", 5, fetchFn)).rejects.toThrow(
      new SearchError("The search could not be run: query is empty."),
    );
  });

  it("falls back to the status when the error detail is not a string", async () => {
    const fetchFn = async () => jsonResponse({ detail: [{ msg: "too long" }] }, 422);
    await expect(search("x", 5, fetchFn)).rejects.toThrow(
      new SearchError("The search could not be run (status 422)."),
    );
  });

  it("falls back to the status when the error body is not JSON", async () => {
    const fetchFn = async () => new Response("Internal Server Error", { status: 500 });
    await expect(search("x", 5, fetchFn)).rejects.toThrow(
      new SearchError("The search could not be run (status 500)."),
    );
  });

  it("reports an unreachable server", async () => {
    const fetchFn = async (): Promise<Response> => {
      throw new TypeError("Failed to fetch");
    };
    await expect(search("x", 5, fetchFn)).rejects.toThrow(
      new SearchError("The server could not be reached."),
    );
  });

  it("reports a successful response whose body is not JSON", async () => {
    const fetchFn = async () => new Response("<html>", { status: 200 });
    await expect(search("x", 5, fetchFn)).rejects.toThrow(
      new SearchError("Unexpected response: the body is not JSON"),
    );
  });
});
