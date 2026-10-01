// Wires the search form to the API and the renderer.

import { type FetchFn, search, SearchError } from "./api.js";
import { renderResults, summaryText } from "./render.js";

export const RESULT_COUNT = 10;

export interface SearchElements {
  form: HTMLFormElement;
  input: HTMLTextAreaElement;
  button: HTMLButtonElement;
  status: HTMLElement;
  results: HTMLElement;
}

function byId<T extends HTMLElement>(doc: Document, id: string, type: { new (): T }): T {
  const node = doc.getElementById(id);
  if (!(node instanceof type)) throw new Error(`page is missing #${id}`);
  return node;
}

export function findElements(doc: Document): SearchElements {
  const view = doc.defaultView;
  if (!view) throw new Error("document has no window");
  return {
    form: byId(doc, "search-form", view.HTMLFormElement),
    input: byId(doc, "query", view.HTMLTextAreaElement),
    button: byId(doc, "search-button", view.HTMLButtonElement),
    status: byId(doc, "status", view.HTMLElement),
    results: byId(doc, "results", view.HTMLElement),
  };
}

function setStatus(status: HTMLElement, message: string, isError = false): void {
  status.textContent = message;
  status.classList.toggle("error", isError);
}

/**
 * Returns the submit handler. A submission while a search is in flight is
 * ignored, so a slow response can never overwrite a newer one.
 */
export function createSearchHandler(
  elements: SearchElements,
  fetchFn: FetchFn,
): (event?: Event) => Promise<void> {
  const { input, button, status, results } = elements;
  let searching = false;

  return async (event) => {
    event?.preventDefault();
    if (searching) return;
    const query = input.value.trim();
    if (!query) {
      setStatus(status, "Describe what you are looking for first.", true);
      return;
    }
    searching = true;
    button.disabled = true;
    setStatus(status, "Searching…");
    try {
      const response = await search(query, RESULT_COUNT, fetchFn);
      renderResults(results, response);
      setStatus(status, summaryText(response));
    } catch (error) {
      results.replaceChildren();
      setStatus(status, error instanceof SearchError ? error.message : "Something went wrong.", true);
    } finally {
      searching = false;
      button.disabled = false;
    }
  };
}

export function initSearch(doc: Document, fetchFn: FetchFn): void {
  const elements = findElements(doc);
  const handler = createSearchHandler(elements, fetchFn);
  elements.form.addEventListener("submit", (event) => void handler(event));
}
