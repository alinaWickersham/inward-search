// DOM rendering for search results. Text from the server is only ever set
// through textContent, so listing copy cannot inject markup.

import { DIMENSION_KEYS, type SearchResponse, type SearchResult } from "./api.js";
import { DIMENSION_LABELS, valueLabel } from "./labels.js";

export function element<K extends keyof HTMLElementTagNameMap>(
  doc: Document,
  tag: K,
  className: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const node = doc.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderResult(doc: Document, result: SearchResult): HTMLElement {
  const { listing } = result;
  const card = element(doc, "article", "result");
  card.dataset.listingId = listing.id;
  if (listing.synthetic) card.append(element(doc, "span", "synthetic", "Synthetic listing"));
  card.append(
    element(doc, "h2", "", listing.name),
    element(doc, "p", "location", listing.location),
    element(doc, "p", "summary", listing.summary),
  );
  const dimensions = element(doc, "ul", "dimensions");
  for (const key of DIMENSION_KEYS) {
    const label = `${DIMENSION_LABELS[key]}: ${valueLabel(listing.dimensions[key])}`;
    dimensions.append(element(doc, "li", "", label));
  }
  card.append(
    dimensions,
    element(doc, "p", "meta", `Rank ${result.rank} · similarity ${result.score.toFixed(3)}`),
  );
  return card;
}

export function renderResults(container: HTMLElement, response: SearchResponse): void {
  const doc = container.ownerDocument;
  container.replaceChildren(...response.results.map((result) => renderResult(doc, result)));
}

export function summaryText(response: SearchResponse): string {
  const count = response.results.length;
  if (count === 0) return "No listings matched.";
  return `${count} ${count === 1 ? "listing" : "listings"}, ranked by similarity to your description.`;
}
