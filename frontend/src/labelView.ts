// DOM for the labelling page. Every control carries a data-action that the
// page controller dispatches on, so the view holds no behaviour of its own.

import { DIMENSION_KEYS } from "./api.js";
import type { GoldQuery, ListingText, QuerySummary } from "./gold.js";
import { DIMENSION_LABELS, DIMENSION_VALUES, TRIAGE_LABELS, valueLabel } from "./labels.js";
import { element } from "./render.js";

function button(doc: Document, text: string, action: string, className = ""): HTMLButtonElement {
  const node = element(doc, "button", className, text);
  node.type = "button";
  node.dataset.action = action;
  return node;
}

export function progressText(summary: QuerySummary): string {
  if (summary.complete) return "done";
  if (summary.pool_size === 0) return summary.triage_set ? "pool not built" : "not started";
  return `${summary.judged} of ${summary.pool_size} judged`;
}

export function renderQueryList(
  list: HTMLElement,
  summaries: QuerySummary[],
  currentId: string | null,
): void {
  const doc = list.ownerDocument;
  list.replaceChildren(
    ...summaries.map((summary) => {
      const open = button(doc, "", "open");
      open.dataset.id = summary.id;
      open.setAttribute("aria-current", String(summary.id === currentId));
      const status = element(doc, "span", summary.complete ? "progress done" : "progress");
      status.textContent = progressText(summary);
      open.append(`${summary.id} · ${summary.text}`, status);
      const item = element(doc, "li", "");
      item.append(open);
      return item;
    }),
  );
}

function renderText(doc: Document, query: GoldQuery): HTMLElement {
  const wrapper = element(doc, "div", "");
  const label = element(doc, "label", "", "Query text");
  label.htmlFor = "query-text";
  const text = element(doc, "textarea", "");
  text.id = "query-text";
  text.rows = 3;
  text.value = query.text;
  text.dataset.action = "text";
  wrapper.append(label, text);
  return wrapper;
}

function renderIntent(doc: Document, query: GoldQuery): HTMLElement {
  const fieldset = element(doc, "fieldset", "");
  fieldset.append(
    element(doc, "legend", "", "Intent"),
    element(
      doc,
      "p",
      "help",
      "Select what the query asks for. Leave a dimension empty for no preference; select more than one value when the query allows either.",
    ),
  );
  for (const key of DIMENSION_KEYS) {
    const row = element(doc, "div", "dimension-row");
    row.append(element(doc, "span", "name", DIMENSION_LABELS[key]));
    for (const value of DIMENSION_VALUES[key]) {
      const chip = button(doc, valueLabel(value), "intent", "chip");
      chip.dataset.dimension = key;
      chip.dataset.value = value;
      chip.setAttribute("aria-pressed", String(query.intent[key].includes(value)));
      row.append(chip);
    }
    fieldset.append(row);
  }
  return fieldset;
}

function renderTriage(doc: Document, query: GoldQuery): HTMLElement {
  const fieldset = element(doc, "fieldset", "");
  fieldset.append(
    element(doc, "legend", "", "Triage class"),
    element(
      doc,
      "p",
      "help",
      "Which support resources should a response offer alongside its results? This never changes the results.",
    ),
  );
  const options: [string, string][] = [["", "Not set"], ...Object.entries(TRIAGE_LABELS)];
  for (const [value, text] of options) {
    const label = element(doc, "label", "triage-option");
    const radio = element(doc, "input", "");
    radio.type = "radio";
    radio.name = "triage";
    radio.value = value;
    radio.checked = (query.triage ?? "") === value;
    radio.dataset.action = "triage";
    label.append(radio, ` ${text}`);
    fieldset.append(label);
  }
  return fieldset;
}

function judgementClass(query: GoldQuery, id: string): string {
  if (!(id in query.judgements)) return "";
  return query.judgements[id] === 1 ? "relevant" : "not-relevant";
}

function renderListing(doc: Document, listing: ListingText): HTMLElement {
  const article = element(doc, "article", "result");
  article.id = "current-listing";
  article.dataset.listingId = listing.id;
  article.append(
    element(doc, "span", "synthetic", "Synthetic listing"),
    element(doc, "h2", "", listing.name),
    element(doc, "p", "location", listing.location),
    element(doc, "p", "summary", listing.summary),
    element(doc, "p", "listing-text", listing.description),
    element(doc, "p", "listing-text", listing.practical),
  );
  return article;
}

function renderJudging(
  doc: Document,
  query: GoldQuery,
  listings: Map<string, ListingText>,
  cursor: number,
): HTMLElement {
  const fieldset = element(doc, "fieldset", "");
  fieldset.append(element(doc, "legend", "", "Relevance"));
  if (query.pool.length === 0) {
    fieldset.append(
      element(
        doc,
        "p",
        "help",
        "Set the intent first. The pool is strategy A's top 20, every listing matching the intent, and near-duplicate partners, shown in a shuffled order.",
      ),
      button(doc, "Build the pool", "build-pool"),
    );
    return fieldset;
  }
  const judged = query.pool.filter((id) => id in query.judgements).length;
  const progress = element(doc, "p", "help", `${judged} of ${query.pool.length} judged`);
  progress.id = "judge-progress";
  const poolList = element(doc, "ol", "");
  poolList.id = "pool-list";
  query.pool.forEach((id, index) => {
    const jump = button(doc, String(index + 1), "jump", judgementClass(query, id));
    jump.dataset.index = String(index);
    jump.setAttribute("aria-current", String(index === cursor));
    jump.setAttribute("aria-label", `Listing ${index + 1} of ${query.pool.length}`);
    const item = element(doc, "li", "");
    item.append(jump);
    poolList.append(item);
  });

  const id = query.pool[cursor];
  const listing = listings.get(id);
  const buttons = element(doc, "div", "judge-buttons");
  const relevant = button(doc, "Relevant (1)", "judge");
  relevant.dataset.grade = "1";
  relevant.setAttribute("aria-pressed", String(query.judgements[id] === 1));
  const notRelevant = button(doc, "Not relevant (0)", "judge", "secondary");
  notRelevant.dataset.grade = "0";
  notRelevant.setAttribute("aria-pressed", String(query.judgements[id] === 0));
  buttons.append(
    relevant,
    notRelevant,
    button(doc, "Previous (k)", "previous", "secondary"),
    button(doc, "Next (j)", "next", "secondary"),
  );

  fieldset.append(
    progress,
    poolList,
    listing ? renderListing(doc, listing) : element(doc, "p", "help", `${id} is not in the corpus`),
    buttons,
    button(doc, "Add candidates for the current intent", "build-pool", "secondary"),
  );
  return fieldset;
}

export function renderEditor(
  editor: HTMLElement,
  query: GoldQuery,
  listings: Map<string, ListingText>,
  cursor: number,
): void {
  const doc = editor.ownerDocument;
  editor.replaceChildren(
    element(doc, "h2", "", query.id),
    renderText(doc, query),
    renderIntent(doc, query),
    renderTriage(doc, query),
    renderJudging(doc, query, listings, cursor),
    button(doc, `Delete ${query.id}`, "delete", "danger"),
  );
}
