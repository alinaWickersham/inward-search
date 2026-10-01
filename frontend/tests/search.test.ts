import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { beforeEach, describe, expect, it, vi } from "vitest";

import { type FetchFn, SEARCH_URL, searchRequest } from "../src/api.js";
import {
  createSearchHandler,
  findElements,
  initSearch,
  RESULT_COUNT,
  type SearchElements,
} from "../src/search.js";
import { jsonResponse, listing, response, result } from "./fixtures.js";

const PAGE = readFileSync(resolve(import.meta.dirname, "../public/index.html"), "utf8");

let elements: SearchElements;

beforeEach(() => {
  // The real page, so a renamed id in index.html fails here.
  document.documentElement.innerHTML = PAGE;
  elements = findElements(document);
});

function deferred(): { promise: Promise<Response>; resolve: (r: Response) => void } {
  let resolve!: (r: Response) => void;
  const promise = new Promise<Response>((r) => (resolve = r));
  return { promise, resolve };
}

describe("the page", () => {
  it("states that the listings are synthetic", () => {
    expect(document.getElementById("synthetic-notice")?.textContent).toContain(
      "Every listing here is synthetic",
    );
  });

  it("is rejected when an element the script needs is missing", () => {
    document.getElementById("status")!.remove();
    expect(() => findElements(document)).toThrow("page is missing #status");
  });
});

describe("createSearchHandler", () => {
  it("asks for a description and does not call the API when the query is blank", async () => {
    const fetchFn = vi.fn<FetchFn>();
    elements.input.value = "   \n ";
    await createSearchHandler(elements, fetchFn)();
    expect(fetchFn).not.toHaveBeenCalled();
    expect(elements.status.textContent).toBe("Describe what you are looking for first.");
    expect(elements.status.classList.contains("error")).toBe(true);
  });

  it("sends the trimmed query and renders the results", async () => {
    const fetchFn = vi.fn<FetchFn>(async () =>
      jsonResponse(response([result(1, 0.9), result(2, 0.4, listing({ id: "L002" }))])),
    );
    elements.input.value = "  somewhere quiet  ";
    await createSearchHandler(elements, fetchFn)();
    expect(fetchFn).toHaveBeenCalledWith(SEARCH_URL, searchRequest("somewhere quiet", RESULT_COUNT));
    expect(elements.results.querySelectorAll("article.result")).toHaveLength(2);
    expect(elements.status.textContent).toBe(
      "2 listings, ranked by similarity to your description.",
    );
    expect(elements.status.classList.contains("error")).toBe(false);
  });

  it("disables the button while searching and ignores a second submit", async () => {
    const pending = deferred();
    const fetchFn = vi.fn<FetchFn>(() => pending.promise);
    const handler = createSearchHandler(elements, fetchFn);
    elements.input.value = "somewhere quiet";

    const first = handler();
    expect(elements.button.disabled).toBe(true);
    expect(elements.status.textContent).toBe("Searching…");
    await handler();
    expect(fetchFn).toHaveBeenCalledTimes(1);

    pending.resolve(jsonResponse(response([result(1, 1)])));
    await first;
    expect(elements.button.disabled).toBe(false);
  });

  it("clears old results and shows the error when a search fails", async () => {
    const ok = vi.fn<FetchFn>(async () => jsonResponse(response([result(1, 1)])));
    elements.input.value = "somewhere quiet";
    await createSearchHandler(elements, ok)();

    const failing: FetchFn = async () => jsonResponse({ detail: "query is empty" }, 422);
    await createSearchHandler(elements, failing)();
    expect(elements.results.children).toHaveLength(0);
    expect(elements.status.textContent).toBe("Search failed: query is empty.");
    expect(elements.status.classList.contains("error")).toBe(true);
    expect(elements.button.disabled).toBe(false);
  });

  it("shows a generic message for an error that is not a search error", async () => {
    const broken = {
      get ok(): boolean {
        throw new TypeError("boom");
      },
    } as Response;
    elements.input.value = "somewhere quiet";
    await createSearchHandler(elements, async () => broken)();
    expect(elements.status.textContent).toBe("Something went wrong.");
  });
});

describe("initSearch", () => {
  it("runs a search when the form is submitted", async () => {
    const fetchFn = vi.fn<FetchFn>(async () => jsonResponse(response([result(1, 1)])));
    initSearch(document, fetchFn);
    elements.input.value = "somewhere quiet";
    elements.form.dispatchEvent(new Event("submit", { cancelable: true }));
    await vi.waitFor(() => expect(elements.status.textContent).toContain("1 listing"));
    expect(fetchFn).toHaveBeenCalledTimes(1);
  });

  it("stops the browser from navigating on submit", () => {
    initSearch(document, vi.fn<FetchFn>());
    const event = new Event("submit", { cancelable: true });
    elements.form.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
  });
});
