import { beforeEach, describe, expect, it } from "vitest";

import { renderResults, summaryText } from "../src/render.js";
import { listing, response, result } from "./fixtures.js";

let container: HTMLElement;

beforeEach(() => {
  document.body.innerHTML = '<section id="results"></section>';
  container = document.getElementById("results")!;
});

function text(card: Element, selector: string): string | null | undefined {
  return card.querySelector(selector)?.textContent;
}

describe("renderResults", () => {
  it("renders one card per result, in rank order", () => {
    renderResults(
      container,
      response([result(1, 0.8234), result(2, 0.5, listing({ id: "L002", name: "Pine Hollow" }))]),
    );
    const cards = container.querySelectorAll("article.result");
    expect([...cards].map((card) => (card as HTMLElement).dataset.listingId)).toEqual([
      "L001",
      "L002",
    ]);
    expect(text(cards[1], "h2")).toBe("Pine Hollow");
  });

  it("shows the listing text, its synthetic label, and its rank and score", () => {
    renderResults(container, response([result(1, 0.8234)]));
    const card = container.querySelector("article.result")!;
    expect(text(card, ".synthetic")).toBe("Synthetic listing");
    expect(text(card, "h2")).toBe("Stillwater House");
    expect(text(card, ".location")).toBe("Invented Valley");
    expect(text(card, ".summary")).toBe("A quiet weekend with light guidance.");
    expect(text(card, ".meta")).toBe("Rank 1 · similarity 0.823");
  });

  it("lists all nine dimensions with reader labels", () => {
    renderResults(container, response([result(1, 1)]));
    const chips = [...container.querySelectorAll(".dimensions li")].map((li) => li.textContent);
    expect(chips).toEqual([
      "Social: solitude",
      "Structure: semi-structured",
      "Speech: full silence",
      "Guidance: light guidance",
      "Physical demand: restful",
      "Tradition: Buddhist-derived",
      "Experience level: newcomer-friendly",
      "Duration: weekend",
      "Cost band: free or donation",
    ]);
  });

  it("omits the synthetic label only when the listing does not carry the flag", () => {
    renderResults(container, response([result(1, 1, listing({ synthetic: false }))]));
    expect(container.querySelector(".synthetic")).toBeNull();
  });

  it("replaces earlier results instead of appending", () => {
    renderResults(container, response([result(1, 1), result(2, 0.5, listing({ id: "L002" }))]));
    renderResults(container, response([result(1, 1, listing({ id: "L009" }))]));
    expect(container.querySelectorAll("article.result")).toHaveLength(1);
  });

  it("treats markup in listing text as text", () => {
    const name = '<img src="x" onerror="alert(1)">';
    renderResults(container, response([result(1, 1, listing({ name }))]));
    expect(container.querySelector("img")).toBeNull();
    expect(text(container, "h2")).toBe(name);
  });
});

describe("summaryText", () => {
  it.each([
    [0, "No listings matched."],
    [1, "1 listing, ranked by similarity to your description."],
    [2, "2 listings, ranked by similarity to your description."],
  ])("describes %i results", (count, expected) => {
    const results = Array.from({ length: count }, (_, i) => result(i + 1, 1));
    expect(summaryText(response(results))).toBe(expected);
  });
});
