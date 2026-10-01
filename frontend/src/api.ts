// Client for POST /api/search. The response is checked at runtime because
// TypeScript types say nothing about what the server actually sent.

export const DIMENSION_KEYS = [
  "social",
  "structure",
  "speech",
  "guidance",
  "physical_demand",
  "tradition",
  "experience_level",
  "duration",
  "cost_band",
] as const;

export type DimensionKey = (typeof DIMENSION_KEYS)[number];

export interface ListingCard {
  id: string;
  name: string;
  location: string;
  summary: string;
  dimensions: Record<DimensionKey, string>;
  synthetic: boolean;
}

export interface SearchResult {
  rank: number;
  score: number;
  listing: ListingCard;
}

export interface SearchResponse {
  query: string;
  strategy: string;
  model: string;
  results: SearchResult[];
}

export type FetchFn = (url: string, init: RequestInit) => Promise<Response>;

export class SearchError extends Error {}

export const SEARCH_URL = "/api/search";

// A POST body rather than a query string, so the text never reaches access logs.
export function searchRequest(query: string, k: number): RequestInit {
  return {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, k }),
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requireType(value: unknown, type: "string" | "number" | "boolean", path: string): void {
  if (typeof value !== type) {
    throw new SearchError(`Unexpected response: ${path} is not a ${type}`);
  }
}

function parseListing(value: unknown, path: string): ListingCard {
  if (!isRecord(value) || !isRecord(value.dimensions)) {
    throw new SearchError(`Unexpected response: ${path} is malformed`);
  }
  for (const key of ["id", "name", "location", "summary"]) {
    requireType(value[key], "string", `${path}.${key}`);
  }
  requireType(value.synthetic, "boolean", `${path}.synthetic`);
  for (const key of DIMENSION_KEYS) {
    requireType(value.dimensions[key], "string", `${path}.dimensions.${key}`);
  }
  return value as unknown as ListingCard;
}

export function parseSearchResponse(data: unknown): SearchResponse {
  if (!isRecord(data) || !Array.isArray(data.results)) {
    throw new SearchError("Unexpected response: results are missing");
  }
  for (const key of ["query", "strategy", "model"]) {
    requireType(data[key], "string", key);
  }
  data.results.forEach((result: unknown, i: number) => {
    if (!isRecord(result)) {
      throw new SearchError(`Unexpected response: results[${i}] is malformed`);
    }
    requireType(result.rank, "number", `results[${i}].rank`);
    requireType(result.score, "number", `results[${i}].score`);
    parseListing(result.listing, `results[${i}].listing`);
  });
  return data as unknown as SearchResponse;
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (isRecord(body) && typeof body.detail === "string") {
      return `The search could not be run: ${body.detail}.`;
    }
  } catch {
    // A body that is not JSON carries nothing worth showing; fall through.
  }
  return `The search could not be run (status ${response.status}).`;
}

export async function search(query: string, k: number, fetchFn: FetchFn): Promise<SearchResponse> {
  let response: Response;
  try {
    response = await fetchFn(SEARCH_URL, searchRequest(query, k));
  } catch {
    throw new SearchError("The server could not be reached.");
  }
  if (!response.ok) {
    throw new SearchError(await errorMessage(response));
  }
  let data: unknown;
  try {
    data = await response.json();
  } catch {
    throw new SearchError("Unexpected response: the body is not JSON");
  }
  return parseSearchResponse(data);
}
