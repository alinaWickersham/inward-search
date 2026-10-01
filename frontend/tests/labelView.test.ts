import { beforeEach, describe, expect, it } from "vitest";

import type { QuerySummary } from "../src/gold.js";
import { progressText, renderEditor, renderQueryList } from "../src/labelView.js";
import { goldQuery, listingText } from "./labelFixtures.js";

let host: HTMLElement;

beforeEach(() => {
  document.body.innerHTML = "<section></section>";
  host = document.querySelector("section")!;
});

function summary(overrides: Partial<QuerySummary> = {}): QuerySummary {
  return { id: "Q001", text: "x", triage_set: false, pool_size: 0, judged: 0, complete: false, ...overrides };
}

describe("progressText", () => {
  it.each([
    [summary(), "not started"],
    [summary({ triage_set: true }), "pool not built"],
    [summary({ pool_size: 30, judged: 7 }), "7 of 30 judged"],
    [summary({ pool_size: 30, judged: 30, complete: true }), "done"],
  ])("describes %o as %s", (s, expected) => {
    expect(progressText(s)).toBe(expected);
  });
});

describe("renderQueryList", () => {
  it("lists each query with its progress and marks the open one", () => {
    renderQueryList(host, [summary(), summary({ id: "Q002", text: "y", complete: true })], "Q002");
    const buttons = [...host.querySelectorAll("button")];
    expect(buttons.map((b) => b.dataset.id)).toEqual(["Q001", "Q002"]);
    expect(buttons[1].getAttribute("aria-current")).toBe("true");
    expect(buttons[1].querySelector(".progress")?.textContent).toBe("done");
  });
});

describe("renderEditor", () => {
  const listings = new Map([["L1", listingText("L1")], ["L2", listingText("L2")]]);

  it("shows the text, pressed intent chips, and the checked triage class", () => {
    const query = goldQuery({
      intent: { ...goldQuery().intent, duration: ["weekend", "week"] },
      triage: "stress_burnout",
    });
    renderEditor(host, query, listings, 0);
    expect(host.querySelector<HTMLTextAreaElement>("#query-text")!.value).toBe("somewhere silent");
    const pressed = [...host.querySelectorAll('[data-action=intent][aria-pressed="true"]')];
    expect(pressed.map((c) => (c as HTMLElement).dataset.value)).toEqual(["weekend", "week"]);
    expect(host.querySelectorAll("[data-action=intent]")).toHaveLength(32);
    expect(host.querySelector<HTMLInputElement>("input[name=triage]:checked")!.value).toBe("stress_burnout");
  });

  it("offers to build the pool before there is one", () => {
    renderEditor(host, goldQuery(), listings, 0);
    expect(host.querySelector("[data-action=build-pool]")?.textContent).toBe("Build the pool");
    expect(host.querySelector("#current-listing")).toBeNull();
  });

  it("shows the listing under the cursor in full, without its annotations", () => {
    const query = goldQuery({ pool: ["L1", "L2"], judgements: { L1: 1 } });
    renderEditor(host, query, listings, 1);
    const card = host.querySelector<HTMLElement>("#current-listing")!;
    expect(card.dataset.listingId).toBe("L2");
    expect(card.textContent).toContain("L2 description");
    expect(card.textContent).toContain("L2 practical");
    expect(card.querySelector(".dimensions")).toBeNull();
    expect(host.querySelector("#judge-progress")?.textContent).toBe("1 of 2 judged");
  });

  it("marks judged pool entries and the current one", () => {
    const query = goldQuery({ pool: ["L1", "L2"], judgements: { L1: 1, L2: 0 } });
    renderEditor(host, query, listings, 0);
    const entries = [...host.querySelectorAll<HTMLElement>("#pool-list button")];
    expect(entries.map((e) => e.className)).toEqual(["relevant", "not-relevant"]);
    expect(entries[0].getAttribute("aria-current")).toBe("true");
    expect(host.querySelector('[data-grade="1"]')?.getAttribute("aria-pressed")).toBe("true");
  });

  it("says so when a pool listing is missing from the corpus", () => {
    renderEditor(host, goldQuery({ pool: ["L9"] }), listings, 0);
    expect(host.textContent).toContain("L9 is not in the corpus");
  });
});
