// Controller for label.html. Every change is saved as soon as it is made,
// so there is no unsaved state to lose.

import { ApiError, type DimensionKey, type FetchFn } from "./api.js";
import {
  addQuery,
  buildPool,
  deleteQuery,
  getListings,
  getQuery,
  type GoldQuery,
  type Grade,
  type ListingText,
  listQueries,
  type QuerySummary,
  saveQuery,
} from "./gold.js";
import { isComplete, judge, nextUnjudged, setTriage, toggleIntentValue } from "./labelState.js";
import { renderEditor, renderQueryList } from "./labelView.js";

export interface LabelElements {
  list: HTMLElement;
  addForm: HTMLFormElement;
  addInput: HTMLTextAreaElement;
  editor: HTMLElement;
  status: HTMLElement;
}

export function findLabelElements(doc: Document): LabelElements {
  const get = (id: string): HTMLElement => {
    const node = doc.getElementById(id);
    if (!node) throw new Error(`page is missing #${id}`);
    return node;
  };
  return {
    list: get("query-list"),
    addForm: get("add-form") as HTMLFormElement,
    addInput: get("new-query") as HTMLTextAreaElement,
    editor: get("editor"),
    status: get("status"),
  };
}

export interface LabelPage {
  start(): Promise<void>;
  /** Resolves when the action in flight, if any, has finished. */
  settled(): Promise<void>;
  current(): GoldQuery | null;
  cursor(): number;
}

function summaryOf(query: GoldQuery): QuerySummary {
  return {
    id: query.id,
    text: query.text,
    triage_set: query.triage !== null,
    pool_size: query.pool.length,
    judged: query.pool.filter((id) => id in query.judgements).length,
    complete: isComplete(query),
  };
}

function isTyping(target: EventTarget | null): boolean {
  return target instanceof Element && target.matches("input, textarea");
}

export function createLabelPage(
  elements: LabelElements,
  fetchFn: FetchFn,
  confirmFn: (message: string) => boolean,
): LabelPage {
  const { list, addForm, addInput, editor, status } = elements;
  let summaries: QuerySummary[] = [];
  let listings = new Map<string, ListingText>();
  let query: GoldQuery | null = null;
  let cursor = 0;
  let busy = false;
  let pending: Promise<void> = Promise.resolve();

  function setStatus(message: string, isError = false): void {
    status.textContent = message;
    status.classList.toggle("error", isError);
  }

  function render(): void {
    renderQueryList(list, summaries, query?.id ?? null);
    if (query) renderEditor(editor, query, listings, cursor);
    else editor.replaceChildren();
  }

  /** Runs one action at a time; input that arrives while one is in flight is dropped. */
  function run(task: () => Promise<void>): void {
    if (busy) return;
    busy = true;
    pending = task()
      .catch((error: unknown) => {
        setStatus(error instanceof ApiError ? error.message : "Something went wrong.", true);
      })
      .finally(() => {
        busy = false;
      });
  }

  function show(updated: GoldQuery, message: string): void {
    query = updated;
    summaries = summaries.map((s) => (s.id === updated.id ? summaryOf(updated) : s));
    render();
    setStatus(message);
  }

  async function open(id: string): Promise<void> {
    const loaded = await getQuery(fetchFn, id);
    cursor = Math.max(nextUnjudged(loaded, -1), 0);
    show(loaded, `${id} loaded.`);
  }

  async function save(updated: GoldQuery): Promise<void> {
    show(await saveQuery(fetchFn, updated), `${updated.id} saved.`);
  }

  async function grade(value: Grade): Promise<void> {
    if (!query || query.pool.length === 0) return;
    const updated = judge(query, query.pool[cursor], value);
    await save(updated);
    const next = nextUnjudged(updated, cursor);
    if (next !== -1) cursor = next;
    render();
    if (next === -1 && query?.triage === null) setStatus("All judged. Set a triage class to finish.");
  }

  function move(delta: number): void {
    if (!query || query.pool.length === 0) return;
    cursor = Math.min(Math.max(cursor + delta, 0), query.pool.length - 1);
    render();
  }

  function onClick(event: Event): void {
    const target = (event.target as Element).closest<HTMLElement>("[data-action]");
    if (!target || !query) return;
    const current = query;
    const { action, dimension, value, grade: gradeValue, index } = target.dataset;
    if (action === "intent") {
      run(() => save(toggleIntentValue(current, dimension as DimensionKey, value!)));
    } else if (action === "build-pool") {
      run(async () => {
        const pooled = await buildPool(fetchFn, current.id);
        cursor = Math.max(nextUnjudged(pooled, -1), 0);
        show(pooled, `${pooled.pool.length} listings to judge.`);
      });
    } else if (action === "judge") {
      run(() => grade(Number(gradeValue) as Grade));
    } else if (action === "jump") {
      move(Number(index) - cursor);
    } else if (action === "previous") {
      move(-1);
    } else if (action === "next") {
      move(1);
    } else if (action === "delete" && confirmFn(`Delete ${current.id}? This removes its file.`)) {
      run(async () => {
        await deleteQuery(fetchFn, current.id);
        summaries = summaries.filter((s) => s.id !== current.id);
        query = null;
        render();
        setStatus(`${current.id} deleted.`);
      });
    }
  }

  function onChange(event: Event): void {
    const target = event.target as HTMLInputElement;
    if (target.dataset.action === "triage" && query) {
      const current = query;
      run(() => save(setTriage(current, target.value || null)));
    }
  }

  function onFocusOut(event: Event): void {
    const target = event.target as HTMLTextAreaElement;
    if (target.dataset.action !== "text" || !query) return;
    const text = target.value.trim();
    if (text && text !== query.text) {
      const current = query;
      run(() => save({ ...current, text }));
    }
  }

  function onKey(event: KeyboardEvent): void {
    if (isTyping(event.target) || event.ctrlKey || event.metaKey || event.altKey) return;
    const actions: Record<string, () => void> = {
      "1": () => run(() => grade(1)),
      "0": () => run(() => grade(0)),
      j: () => move(1),
      ArrowRight: () => move(1),
      k: () => move(-1),
      ArrowLeft: () => move(-1),
    };
    const action = actions[event.key];
    if (action) {
      event.preventDefault();
      action();
    }
  }

  function onListClick(event: Event): void {
    const target = (event.target as Element).closest<HTMLElement>("[data-action=open]");
    if (target?.dataset.id) {
      const id = target.dataset.id;
      run(() => open(id));
    }
  }

  function onAdd(event: Event): void {
    event.preventDefault();
    const text = addInput.value.trim();
    if (!text) {
      setStatus("Write the query first.", true);
      return;
    }
    run(async () => {
      const created = await addQuery(fetchFn, text);
      addInput.value = "";
      summaries = [...summaries, summaryOf(created)];
      cursor = 0;
      show(created, `${created.id} added.`);
    });
  }

  editor.addEventListener("click", onClick);
  editor.addEventListener("change", onChange);
  editor.addEventListener("focusout", onFocusOut);
  list.addEventListener("click", onListClick);
  addForm.addEventListener("submit", onAdd);
  editor.ownerDocument.addEventListener("keydown", onKey);

  return {
    async start() {
      run(async () => {
        listings = new Map((await getListings(fetchFn)).map((item) => [item.id, item]));
        summaries = await listQueries(fetchFn);
        const first = summaries.find((s) => !s.complete) ?? summaries[0];
        if (first) {
          await open(first.id);
        } else {
          render();
          setStatus("No queries yet. Add one to begin.");
        }
      });
      await pending;
    },
    settled: () => pending,
    current: () => query,
    cursor: () => cursor,
  };
}
