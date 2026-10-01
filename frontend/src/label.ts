// Entry point loaded by label.html.

import { createLabelPage, findLabelElements } from "./labelPage.js";

void createLabelPage(
  findLabelElements(document),
  (url, init) => fetch(url, init),
  (message) => window.confirm(message),
).start();
