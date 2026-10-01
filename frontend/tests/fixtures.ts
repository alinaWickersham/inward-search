import type { ListingCard, SearchResponse, SearchResult } from "../src/api.js";

export function listing(overrides: Partial<ListingCard> = {}): ListingCard {
  return {
    id: "L001",
    name: "Stillwater House",
    location: "Invented Valley",
    summary: "A quiet weekend with light guidance.",
    dimensions: {
      social: "solitude",
      structure: "semi_structured",
      speech: "full_silence",
      guidance: "light_guidance",
      physical_demand: "restful",
      tradition: "buddhist_derived",
      experience_level: "newcomer_friendly",
      duration: "weekend",
      cost_band: "free_or_donation",
    },
    synthetic: true,
    ...overrides,
  };
}

export function result(rank: number, score: number, card: ListingCard = listing()): SearchResult {
  return { rank, score, listing: card };
}

export function response(results: SearchResult[]): SearchResponse {
  return { query: "somewhere quiet", strategy: "embedding", model: "test-model", results };
}

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}
