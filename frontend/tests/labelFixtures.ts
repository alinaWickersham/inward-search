import type { FetchFn } from "../src/api.js";
import type { GoldQuery, ListingText } from "../src/gold.js";
import { isComplete } from "../src/labelState.js";
import { jsonResponse } from "./fixtures.js";

export function emptyIntent(): GoldQuery["intent"] {
  return {
    social: [],
    structure: [],
    speech: [],
    guidance: [],
    physical_demand: [],
    tradition: [],
    experience_level: [],
    duration: [],
    cost_band: [],
  };
}

export function goldQuery(overrides: Partial<GoldQuery> = {}): GoldQuery {
  return {
    id: "Q001",
    text: "somewhere silent",
    intent: emptyIntent(),
    triage: null,
    pool: [],
    pool_provenance: null,
    judgements: {},
    ...overrides,
  };
}

export function listingText(id: string): ListingText {
  return {
    id,
    name: `Listing ${id}`,
    location: "Invented Valley",
    summary: `${id} summary`,
    description: `${id} description`,
    practical: `${id} practical`,
  };
}

/**
 * An in-memory stand-in for the labelling API with the same routes and the
 * same rules the Python app enforces. `pool` is what building a pool adds.
 */
export function fakeLabelServer(queries: GoldQuery[], pool: string[]) {
  const store = new Map(queries.map((q) => [q.id, structuredClone(q)]));
  const listings = pool.map(listingText);
  const requests: { method: string; url: string }[] = [];

  const fetchFn: FetchFn = async (url, init) => {
    const method = init.method ?? "GET";
    requests.push({ method, url });
    const body = init.body ? JSON.parse(init.body as string) : null;
    const id = url.split("/")[3];
    if (url === "/api/listings") return jsonResponse(listings);
    if (url === "/api/gold" && method === "GET") {
      return jsonResponse(
        [...store.values()].map((q) => ({
          id: q.id,
          text: q.text,
          triage_set: q.triage !== null,
          pool_size: q.pool.length,
          judged: Object.keys(q.judgements).length,
          complete: isComplete(q),
        })),
      );
    }
    if (url === "/api/gold" && method === "POST") {
      const created = goldQuery({ id: `Q${String(store.size + 1).padStart(3, "0")}`, text: body.text });
      store.set(created.id, created);
      return jsonResponse(created, 201);
    }
    const stored = store.get(id);
    if (!stored) return jsonResponse({ detail: `no query ${id}` }, 404);
    if (url.endsWith("/pool")) {
      stored.pool = [...stored.pool, ...pool.filter((lid) => !stored.pool.includes(lid))];
      return jsonResponse(stored);
    }
    if (method === "PUT") {
      if (JSON.stringify(body.pool) !== JSON.stringify(stored.pool)) {
        return jsonResponse({ detail: "the pool changed; reload the query" }, 409);
      }
      store.set(id, body);
      return jsonResponse(body);
    }
    if (method === "DELETE") {
      store.delete(id);
      return new Response(null, { status: 204 });
    }
    return jsonResponse(stored);
  };
  return { fetchFn, store, requests };
}
