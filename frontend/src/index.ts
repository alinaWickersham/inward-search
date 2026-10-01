// Entry point loaded by index.html.

import { initSearch } from "./search.js";

initSearch(document, (url, init) => fetch(url, init));
