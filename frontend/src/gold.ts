// Client for the labelling API in src/threshold/api/label.py.

import {
  ApiError,
  DIMENSION_KEYS,
  type DimensionKey,
  type FetchFn,
  isRecord,
  requestJson,
  requireType,
} from "./api.js";

export type Grade = 0 | 1;

export type GoldIntent = Record<DimensionKey, string[]>;

export interface GoldQuery {
  id: string;
  text: string;
  intent: GoldIntent;
  triage: string | null;
  pool: string[];
  pool_provenance: { embedding_model: string; embedding_depth: number } | null;
  judgements: Record<string, Grade>;
}

export interface QuerySummary {
  id: string;
  text: string;
  triage_set: boolean;
  pool_size: number;
  judged: number;
  complete: boolean;
}

export interface ListingText {
  id: string;
  name: string;
  location: string;
  summary: string;
  description: string;
  practical: string;
}

const JSON_HEADERS = { "Content-Type": "application/json" };

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

export function parseGoldQuery(data: unknown): GoldQuery {
  if (!isRecord(data) || !isRecord(data.intent) || !isRecord(data.judgements)) {
    throw new ApiError("Unexpected response: query is malformed");
  }
  requireType(data.id, "string", "id");
  requireType(data.text, "string", "text");
  if (data.triage !== null) requireType(data.triage, "string", "triage");
  if (!isStringArray(data.pool)) throw new ApiError("Unexpected response: pool is malformed");
  for (const key of DIMENSION_KEYS) {
    if (!isStringArray(data.intent[key])) {
      throw new ApiError(`Unexpected response: intent.${key} is malformed`);
    }
  }
  for (const grade of Object.values(data.judgements)) {
    if (grade !== 0 && grade !== 1) {
      throw new ApiError("Unexpected response: a judgement is not 0 or 1");
    }
  }
  return data as unknown as GoldQuery;
}

function parseList<T>(data: unknown, keys: string[], what: string): T[] {
  if (!Array.isArray(data) || !data.every((item) => isRecord(item) && keys.every((k) => k in item))) {
    throw new ApiError(`Unexpected response: ${what} are malformed`);
  }
  return data as T[];
}

export async function listQueries(fetchFn: FetchFn): Promise<QuerySummary[]> {
  const data = await requestJson(fetchFn, "/api/gold", { method: "GET" }, "Loading queries");
  return parseList(data, ["id", "text", "complete", "judged", "pool_size"], "queries");
}

export async function getListings(fetchFn: FetchFn): Promise<ListingText[]> {
  const data = await requestJson(fetchFn, "/api/listings", { method: "GET" }, "Loading listings");
  return parseList(data, ["id", "name", "description", "practical"], "listings");
}

export async function getQuery(fetchFn: FetchFn, id: string): Promise<GoldQuery> {
  const data = await requestJson(fetchFn, `/api/gold/${id}`, { method: "GET" }, "Loading");
  return parseGoldQuery(data);
}

export async function addQuery(fetchFn: FetchFn, text: string): Promise<GoldQuery> {
  const init = { method: "POST", headers: JSON_HEADERS, body: JSON.stringify({ text }) };
  return parseGoldQuery(await requestJson(fetchFn, "/api/gold", init, "Adding"));
}

export async function saveQuery(fetchFn: FetchFn, query: GoldQuery): Promise<GoldQuery> {
  const init = { method: "PUT", headers: JSON_HEADERS, body: JSON.stringify(query) };
  return parseGoldQuery(await requestJson(fetchFn, `/api/gold/${query.id}`, init, "Saving"));
}

export async function buildPool(fetchFn: FetchFn, id: string): Promise<GoldQuery> {
  const data = await requestJson(fetchFn, `/api/gold/${id}/pool`, { method: "POST" }, "Pooling");
  return parseGoldQuery(data);
}

export async function deleteQuery(fetchFn: FetchFn, id: string): Promise<void> {
  await requestJson(fetchFn, `/api/gold/${id}`, { method: "DELETE" }, "Deleting");
}
