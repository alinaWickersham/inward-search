import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { beforeEach, describe, expect, it, vi } from "vitest";

import { createLabelPage, findLabelElements, type LabelPage } from "../src/labelPage.js";
import { fakeLabelServer, goldQuery } from "./labelFixtures.js";

const PAGE = readFileSync(resolve(import.meta.dirname, "../public/label.html"), "utf8");

beforeEach(() => {
  document.documentElement.innerHTML = PAGE;
});

async function startPage(queries = [goldQuery()], pool = ["L1", "L2", "L3"]) {
  const server = fakeLabelServer(queries, pool);
  const confirm = vi.fn(() => true);
  const page = createLabelPage(findLabelElements(document), server.fetchFn, confirm);
  await page.start();
  return { page, server, confirm };
}

function click(selector: string): void {
  document.querySelector<HTMLElement>(selector)!.click();
}

function key(k: string, target: EventTarget = document.body): void {
  target.dispatchEvent(new KeyboardEvent("keydown", { key: k, bubbles: true }));
}

const status = () => document.getElementById("status")!.textContent;

async function act(page: LabelPage, action: () => void): Promise<void> {
  action();
  await page.settled();
}

describe("the label page", () => {
  it("states that the listings are synthetic", () => {
    expect(document.getElementById("synthetic-notice")?.textContent).toContain("Every listing here is synthetic");
  });

  it("is rejected when an element the script needs is missing", () => {
    document.getElementById("editor")!.remove();
    expect(() => findLabelElements(document)).toThrow("page is missing #editor");
  });
});

describe("starting", () => {
  it("opens the first query that is not complete", async () => {
    const done = goldQuery({ id: "Q001", triage: "seeking", pool: ["L1"], judgements: { L1: 1 } });
    const { page } = await startPage([done, goldQuery({ id: "Q002" })]);
    expect(page.current()?.id).toBe("Q002");
    expect(document.querySelectorAll("#query-list button")).toHaveLength(2);
  });

  it("asks for a first query when there are none", async () => {
    await startPage([]);
    expect(status()).toBe("No queries yet. Add one to begin.");
  });
});

describe("labelling a query", () => {
  it("saves an intent chip as soon as it is pressed", async () => {
    const { page, server } = await startPage();
    await act(page, () => click('[data-dimension=speech][data-value=full_silence]'));
    expect(server.store.get("Q001")!.intent.speech).toEqual(["full_silence"]);
    expect(document.querySelector('[data-value=full_silence]')?.getAttribute("aria-pressed")).toBe("true");
    expect(status()).toBe("Q001 saved.");
  });

  it("saves the triage class, and clears it with Not set", async () => {
    const { page, server } = await startPage();
    const choose = (value: string) => {
      const radio = document.querySelector<HTMLInputElement>(`input[name=triage][value="${value}"]`)!;
      radio.checked = true;
      radio.dispatchEvent(new Event("change", { bubbles: true }));
    };
    await act(page, () => choose("possible_clinical_need"));
    expect(server.store.get("Q001")!.triage).toBe("possible_clinical_need");
    await act(page, () => choose(""));
    expect(server.store.get("Q001")!.triage).toBeNull();
  });

  it("saves edited text when the box loses focus, and ignores a blank edit", async () => {
    const { page, server } = await startPage();
    const box = document.querySelector<HTMLTextAreaElement>("#query-text")!;
    box.value = "  somewhere very silent ";
    await act(page, () => box.dispatchEvent(new FocusEvent("focusout", { bubbles: true })));
    expect(server.store.get("Q001")!.text).toBe("somewhere very silent");
    const again = document.querySelector<HTMLTextAreaElement>("#query-text")!;
    again.value = "   ";
    await act(page, () => again.dispatchEvent(new FocusEvent("focusout", { bubbles: true })));
    expect(server.store.get("Q001")!.text).toBe("somewhere very silent");
  });

  it("builds the pool and shows the first listing", async () => {
    const { page } = await startPage();
    await act(page, () => click("[data-action=build-pool]"));
    expect(page.current()?.pool).toEqual(["L1", "L2", "L3"]);
    expect(document.querySelector<HTMLElement>("#current-listing")!.dataset.listingId).toBe("L1");
    expect(status()).toBe("3 listings to judge.");
  });
});

describe("judging with the keyboard", () => {
  async function pooledPage() {
    const started = await startPage([goldQuery({ pool: ["L1", "L2", "L3"] })]);
    return started;
  }

  it("1 and 0 save a grade and move to the next unjudged listing", async () => {
    const { page, server } = await pooledPage();
    await act(page, () => key("1"));
    expect(page.cursor()).toBe(1);
    await act(page, () => key("0"));
    expect(server.store.get("Q001")!.judgements).toEqual({ L1: 1, L2: 0 });
    expect(page.cursor()).toBe(2);
    expect(document.querySelector("#judge-progress")?.textContent).toBe("2 of 3 judged");
  });

  it("re-judging a listing overwrites its grade", async () => {
    const { page, server } = await pooledPage();
    await act(page, () => key("1"));
    await act(page, () => key("k"));
    await act(page, () => key("0"));
    expect(server.store.get("Q001")!.judgements.L1).toBe(0);
  });

  it("j and k move without saving, and stop at the ends", async () => {
    const { page, server } = await pooledPage();
    key("k");
    expect(page.cursor()).toBe(0);
    key("j");
    key("ArrowRight");
    key("j");
    expect(page.cursor()).toBe(2);
    expect(server.requests.filter((r) => r.method === "PUT")).toHaveLength(0);
  });

  it("ignores keys typed into a text box", async () => {
    const { page, server } = await pooledPage();
    key("1", document.querySelector("#query-text")!);
    await page.settled();
    expect(server.store.get("Q001")!.judgements).toEqual({});
  });

  it("drops a second keypress while a save is in flight", async () => {
    const { page, server } = await pooledPage();
    key("1");
    key("1");
    await page.settled();
    expect(server.requests.filter((r) => r.method === "PUT")).toHaveLength(1);
  });

  it("says when everything is judged but triage is still missing", async () => {
    const { page } = await startPage([goldQuery({ pool: ["L1"] })]);
    await act(page, () => key("1"));
    expect(status()).toBe("All judged. Set a triage class to finish.");
  });

  it("marks the query done in the list when it is complete", async () => {
    const { page } = await startPage([goldQuery({ pool: ["L1"], triage: "seeking" })]);
    await act(page, () => key("1"));
    expect(document.querySelector("#query-list .progress")?.textContent).toBe("done");
  });

  it("jumps to a pool entry when it is clicked", async () => {
    const { page } = await pooledPage();
    click('#pool-list [data-index="2"]');
    expect(page.cursor()).toBe(2);
  });
});

describe("adding, switching, and deleting", () => {
  it("adds a query and opens it", async () => {
    const { page, server } = await startPage();
    document.querySelector<HTMLTextAreaElement>("#new-query")!.value = "a quiet week alone";
    await act(page, () => document.getElementById("add-form")!.dispatchEvent(new Event("submit", { cancelable: true })));
    expect(page.current()?.text).toBe("a quiet week alone");
    expect(server.store.has("Q002")).toBe(true);
    expect(document.querySelector<HTMLTextAreaElement>("#new-query")!.value).toBe("");
  });

  it("refuses to add a blank query", async () => {
    const { page, server } = await startPage();
    await act(page, () => document.getElementById("add-form")!.dispatchEvent(new Event("submit", { cancelable: true })));
    expect(status()).toBe("Write the query first.");
    expect(server.store.size).toBe(1);
  });

  it("opens another query from the list", async () => {
    const { page } = await startPage([goldQuery(), goldQuery({ id: "Q002", text: "other" })]);
    await act(page, () => click('#query-list [data-id="Q002"]'));
    expect(page.current()?.id).toBe("Q002");
  });

  it("deletes only after confirmation", async () => {
    const { page, server, confirm } = await startPage();
    confirm.mockReturnValueOnce(false);
    await act(page, () => click("[data-action=delete]"));
    expect(server.store.has("Q001")).toBe(true);
    await act(page, () => click("[data-action=delete]"));
    expect(server.store.has("Q001")).toBe(false);
    expect(page.current()).toBeNull();
    expect(document.querySelectorAll("#query-list button")).toHaveLength(0);
  });

  it("shows a server error and keeps the page usable", async () => {
    const { page, server } = await startPage();
    server.store.get("Q001")!.pool = ["L1"]; // the stored pool moved on under the page
    await act(page, () => click('[data-dimension=speech][data-value=dialogue]'));
    expect(status()).toBe("Saving failed: the pool changed; reload the query.");
    expect(document.getElementById("status")!.classList.contains("error")).toBe(true);
    await act(page, () => click('#query-list [data-id="Q001"]'));
    expect(page.current()?.pool).toEqual(["L1"]);
  });
});
