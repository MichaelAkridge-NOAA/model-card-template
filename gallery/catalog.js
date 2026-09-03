(function () {
  "use strict";
  const data = JSON.parse(document.getElementById("catalog-data").textContent);
  const params = new URLSearchParams(location.search);
  const state = {
    source: data.sources[params.get("catalog")] ? params.get("catalog") : data.default_source,
    query: params.get("q") || "",
    sort: params.get("sort") || "name",
    selectedModel: params.get("model") || "",
    filters: new Map()
  };
  const quickFacets = ["domain", "task", "formats", "commercial_use"];
  const facetLabels = { domain: "Domain", task: "Task", formats: "Format", family: "Family", geo_regions: "Region", license: "License", commercial_use: "Commercial use", ai4g_relationship: "AI4G relationship", datasets: "Dataset" };
  const sourceButtons = Array.from(document.querySelectorAll("[data-source]"));
  const search = document.getElementById("catalog-search");
  const sort = document.getElementById("sort-models");
  const grid = document.getElementById("catalog-grid");
  const empty = document.getElementById("empty-state");
  const selectedModel = document.getElementById("selected-model");
  const sourceAbout = document.getElementById("source-about");
  const licenseDialog = document.getElementById("license-dialog");

  function values(model, facet) {
    const value = model[facet];
    return Array.isArray(value) ? value : value ? [value] : [];
  }

  function label(value) {
    return String(value).replaceAll("_", " ").replaceAll("-", " ").replace(/\b\w/g, character => character.toUpperCase());
  }

  function activeModels() {
    return data.sources[state.source].models.filter(model => model.status === "active");
  }

  function matches(model) {
    const haystack = [model.display_name, model.description, model.developer, model.owner, ...model.tags, ...model.datasets, ...model.labels, ...model.family].join(" ").toLowerCase();
    if (state.query && !state.query.toLowerCase().split(/\s+/).every(term => haystack.includes(term))) return false;
    for (const [facet, selected] of state.filters) {
      if (selected.size && !values(model, facet).some(value => selected.has(String(value)))) return false;
    }
    return true;
  }

  function setFilter(facet, value, exclusive) {
    const selected = state.filters.get(facet) || new Set();
    const wasSelected = selected.has(value);
    if (exclusive) {
      selected.clear();
      if (!wasSelected) selected.add(value);
    } else {
      wasSelected ? selected.delete(value) : selected.add(value);
    }
    selected.size ? state.filters.set(facet, selected) : state.filters.delete(facet);
    render();
  }

  function syncUrl() {
    const next = new URLSearchParams();
    next.set("catalog", state.source);
    if (state.query) next.set("q", state.query);
    if (state.sort !== "name") next.set("sort", state.sort);
    if (state.selectedModel) next.set("model", state.selectedModel);
    for (const [facet, selected] of state.filters) next.set(`f_${facet}`, Array.from(selected).join(","));
    history.replaceState(null, "", `${location.pathname}?${next.toString()}`);
  }

  function restoreFilters() {
    state.filters.clear();
    for (const [key, value] of params) {
      if (key.startsWith("f_") && value) state.filters.set(key.slice(2), new Set(value.split(",")));
    }
  }

  function statButton(value, title, detail, icon, facet, filterValue) {
    const selected = facet && state.filters.get(facet)?.has(filterValue);
    const action = facet ? (selected ? "Selected filter. Select to clear" : "Select to filter models") : "Select to clear all filters";
    return `<button class="stat-card" type="button" data-stat-facet="${facet || ""}" data-stat-value="${filterValue || ""}" aria-pressed="${Boolean(selected)}" aria-label="${value} ${title}. ${detail}. ${action}."><span class="stat-icon">${icon}</span><strong class="stat-value">${value} ${title}</strong><span class="stat-label">${detail}</span><span class="stat-cta">${action} &gt;</span></button>`;
  }

  function renderHeader() {
    const source = data.sources[state.source];
    const totals = source.totals;
    document.getElementById("inventory-copy").textContent = `${totals.total} active models spanning ${[totals.detectors && "detection", totals.classifiers && "classification", totals.segmenters && "segmentation", totals.encoders && "encoding", totals.cascades && "cascades"].filter(Boolean).join(", ")}.`;
    sourceButtons.forEach(button => {
      const selected = button.dataset.source === state.source;
      button.setAttribute("aria-selected", String(selected));
      button.tabIndex = selected ? 0 : -1;
    });
    const readyDetail = state.source === "sparrow" ? "Unflavored ONNX defaults" : "Reviewed with card and artifacts";
    document.getElementById("stat-grid").innerHTML = [
      statButton(totals.total, "total", "Active catalog entries", "#"),
      statButton(totals.detectors, "detectors", "Locate subjects in imagery or audio", "◎", "task", "detector"),
      statButton(totals.classifiers, "classifiers", "Identify classes or species", "▦", "task", "classifier"),
      statButton(totals.ready, source.ready_label, readyDetail, "✓", state.source === "nmfs-osi" ? "catalog_ready" : "default_onnx", "true")
    ].join("");
    document.querySelectorAll("[data-stat-facet]").forEach(button => button.addEventListener("click", () => {
      if (!button.dataset.statFacet) {
        state.filters.clear();
        render();
      } else {
        setFilter(button.dataset.statFacet, button.dataset.statValue, true);
      }
    }));
    document.getElementById("source-note").textContent = `${source.description} ${source.freshness}.`;
    const sourceLink = document.getElementById("source-link");
    sourceLink.href = source.source_url;
    if (source.about && source.project_url) {
      document.getElementById("source-about-title").textContent = source.about_title;
      document.getElementById("source-about-text").textContent = source.about;
      document.getElementById("source-project-link").href = source.project_url;
      sourceAbout.hidden = false;
    } else {
      sourceAbout.hidden = true;
    }
  }

  function availableFacets() {
    const common = ["domain", "task", "formats", "family", "geo_regions", "license", "commercial_use"];
    return state.source === "sparrow" ? [...common, "ai4g_relationship"] : [...common, "datasets"];
  }

  function facetCounts(facet) {
    const counts = new Map();
    activeModels().forEach(model => values(model, facet).forEach(value => counts.set(String(value), (counts.get(String(value)) || 0) + 1)));
    return Array.from(counts).sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]));
  }

  function filterButton(facet, value, count) {
    const pressed = state.filters.get(facet)?.has(value) || false;
    return `<button class="chip" type="button" data-facet="${facet}" data-value="${escapeHtml(value)}" aria-pressed="${pressed}" aria-label="${label(value)}, ${count} models">${label(value)} <span class="chip-count">${count}</span></button>`;
  }

  function bindFilterButtons() {
    document.querySelectorAll("[data-facet]").forEach(button => button.addEventListener("click", () => setFilter(button.dataset.facet, button.dataset.value, false)));
  }

  function renderFacets() {
    const facets = availableFacets();
    document.getElementById("quick-filters").innerHTML = facets.filter(facet => quickFacets.includes(facet)).flatMap(facet => facetCounts(facet).slice(0, facet === "domain" ? 6 : 8).map(([value, count]) => filterButton(facet, value, count))).join("");
    document.getElementById("facet-groups").innerHTML = facets.filter(facet => !quickFacets.includes(facet)).map(facet => `<section class="facet-group"><h3>${facetLabels[facet]}</h3><div class="facet-options">${facetCounts(facet).slice(0, 24).map(([value, count]) => filterButton(facet, value, count)).join("")}</div></section>`).join("");
    bindFilterButtons();
  }

  function escapeHtml(value) {
    const node = document.createElement("span");
    node.textContent = value == null ? "" : String(value);
    return node.innerHTML;
  }

  function referenceUrl(reference) {
    return (reference.match(/https?:\/\/[^\s;]+/) || [""])[0].replace(/[.,)]$/, "");
  }

  function cardHtml(model) {
    const sourceIsNmfs = state.source === "nmfs-osi";
    const icon = { detector: "◎", classifier: "▦", segmenter: "◫", encoder: "◆", cascade: "↳" }[model.task] || "·";
    const selected = state.selectedModel === model.catalog_id;
    const reference = model.source_url || referenceUrl(model.reference);
    const actions = [];
    if (sourceIsNmfs && model.card_url) actions.push(`<a class="action primary" href="${escapeHtml(model.card_url)}">Model Card</a>`);
    if (reference) actions.push(`<a class="action${sourceIsNmfs ? "" : " primary"}" href="${escapeHtml(reference)}" target="_blank" rel="noopener noreferrer">${sourceIsNmfs ? "Hugging Face" : "Reference"}</a>`);
    actions.push(`<button class="action license-action" type="button" data-license-id="${escapeHtml(model.catalog_id)}">License</button>`);
    const classMeta = model.class_count ? `${model.class_count} ${model.class_count === 1 ? "class" : "classes"}` : (model.labels.length ? `${model.labels.length} classes` : "Not listed");
    const family = model.family.length ? model.family.join(" / ") : "Not listed";
    const architecture = model.architecture || "Not listed";
    const input = model.input_size || "Not listed";
    const formats = model.formats.map(format => `<span class="badge format-badge">${label(format)}</span>`).join("");
    return `<article class="model-card${selected ? " selected" : ""}" data-model-id="${escapeHtml(model.catalog_id)}"><div class="card-head"><span class="task-icon task-${model.task}" role="img" aria-label="${label(model.task)}">${icon}</span><div><h2 class="card-title">${escapeHtml(model.display_name)}</h2><div class="badges"><span class="badge badge-task badge-${model.task}">${label(model.task)}</span><span class="badge badge-domain">${label(model.domain)}</span>${model.geo_scope !== "unknown" ? `<span class="badge badge-scope">${label(model.geo_scope)}</span>` : ""}</div></div><button class="select-model" type="button" data-select-id="${escapeHtml(model.catalog_id)}" aria-pressed="${selected}" aria-label="${selected ? "Clear selection" : "Select"} ${escapeHtml(model.display_name)}" title="${selected ? "Clear selection" : "Select model"}"><span class="select-symbol">${selected ? "✓" : "+"}</span><span class="select-label">${selected ? "Selected" : "Select"}</span></button></div><p class="card-description">${escapeHtml(model.description || "Catalog entry; follow the source reference for model details.")}</p><dl class="model-facts"><div><dt>Classes</dt><dd>${escapeHtml(classMeta)}</dd></div><div><dt>Family</dt><dd>${escapeHtml(family)}</dd></div><div><dt>Architecture</dt><dd>${escapeHtml(architecture)}</dd></div><div><dt>Input</dt><dd>${escapeHtml(input)}</dd></div></dl><div class="format-row"><span class="format-label">Formats</span>${formats || `<span class="badge format-badge">Not listed</span>`}</div><div class="actions">${actions.join("")}</div><div class="status-row"><span class="status available">${sourceIsNmfs ? "Source available" : "Pinned catalog"}</span><span class="status license">${escapeHtml(model.license)}</span>${model.flavor ? `<span class="status warning">${escapeHtml(model.flavor)}</span>` : ""}</div><p class="developer">Developer: ${escapeHtml(model.developer)}</p></article>`;
  }

  function renderSelection(models) {
    const model = models.find(item => item.catalog_id === state.selectedModel);
    if (!model) {
      state.selectedModel = "";
      selectedModel.hidden = true;
      selectedModel.innerHTML = "";
      return;
    }
    const sourceIsNmfs = state.source === "nmfs-osi";
    const reference = model.source_url || referenceUrl(model.reference);
    const primaryUrl = sourceIsNmfs && model.card_url ? model.card_url : reference;
    const primaryLabel = sourceIsNmfs && model.card_url ? "View Model Card" : "View Reference";
    const family = model.family.length ? model.family.join(" / ") : "Family not listed";
    selectedModel.innerHTML = `<div class="selected-copy"><p class="eyebrow">Selected model</p><h2>${escapeHtml(model.display_name)}</h2><p>${label(model.task)} · ${escapeHtml(family)} · ${escapeHtml(model.license)}</p></div><div class="selected-actions">${primaryUrl ? `<a class="action primary" href="${escapeHtml(primaryUrl)}"${sourceIsNmfs ? "" : ` target="_blank" rel="noopener noreferrer"`}>${primaryLabel}</a>` : ""}${reference && primaryUrl !== reference ? `<a class="action" href="${escapeHtml(reference)}" target="_blank" rel="noopener noreferrer">View Source</a>` : ""}<button id="clear-selection" class="quiet-button" type="button">Clear selection</button></div>`;
    selectedModel.hidden = false;
    document.getElementById("clear-selection").addEventListener("click", () => {
      state.selectedModel = "";
      render();
    });
  }

  function renderCards() {
    const models = activeModels().filter(matches);
    if (state.selectedModel && !models.some(model => model.catalog_id === state.selectedModel)) state.selectedModel = "";
    models.sort((left, right) => state.sort === "task" ? left.task.localeCompare(right.task) || left.display_name.localeCompare(right.display_name) : state.sort === "updated" ? (right.last_modified || "").localeCompare(left.last_modified || "") : left.display_name.localeCompare(right.display_name));
    grid.innerHTML = models.map(cardHtml).join("");
    renderSelection(models);
    empty.hidden = models.length !== 0;
    document.getElementById("result-count").textContent = `Showing ${models.length} of ${activeModels().length} models`;
    document.querySelectorAll(".license-action").forEach(button => button.addEventListener("click", () => showLicense(button.dataset.licenseId)));
    document.querySelectorAll(".select-model").forEach(button => button.addEventListener("click", () => {
      state.selectedModel = state.selectedModel === button.dataset.selectId ? "" : button.dataset.selectId;
      render();
      if (state.selectedModel) selectedModel.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }));
  }

  function showLicense(catalogId) {
    const model = activeModels().find(item => item.catalog_id === catalogId);
    document.getElementById("license-title").textContent = model.display_name;
    document.getElementById("license-content").innerHTML = `<dt>Model license</dt><dd>${escapeHtml(model.license)}</dd><dt>Dataset license</dt><dd>${escapeHtml(model.dataset_license)}</dd><dt>Commercial use</dt><dd>${label(model.commercial_use)}</dd><dt>Policy reason</dt><dd>${escapeHtml(model.commercial_use_reason)}</dd><dt>Source</dt><dd>${escapeHtml(model.source_id)}</dd>`;
    licenseDialog.showModal();
  }

  function render() {
    const allowed = new Set(availableFacets().concat("catalog_ready", "default_onnx"));
    for (const facet of state.filters.keys()) if (!allowed.has(facet)) state.filters.delete(facet);
    renderHeader();
    renderFacets();
    renderCards();
    syncUrl();
  }

  sourceButtons.forEach(button => {
    button.addEventListener("click", () => { state.source = button.dataset.source; state.filters.clear(); state.selectedModel = ""; render(); });
    button.addEventListener("keydown", event => {
      if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
      event.preventDefault();
      const next = button.dataset.source === "nmfs-osi" ? "sparrow" : "nmfs-osi";
      document.querySelector(`[data-source="${next}"]`).click();
      document.querySelector(`[data-source="${next}"]`).focus();
    });
  });
  search.value = state.query;
  sort.value = state.sort;
  search.addEventListener("input", event => { state.query = event.target.value.trim(); render(); });
  sort.addEventListener("change", event => { state.sort = event.target.value; render(); });
  document.getElementById("reset-filters").addEventListener("click", () => { state.query = ""; state.filters.clear(); search.value = ""; render(); });
  window.addEventListener("popstate", () => location.reload());
  restoreFilters();
  render();
}());