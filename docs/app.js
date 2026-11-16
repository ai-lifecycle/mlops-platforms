(function () {
  "use strict";

  const state = {
    tools: [],
    search: "",
    license: "all",
    job: "all",
    compliance: "all",
    caps: new Set(),
    compare: ["mlflow", "kubeflow", "weights-and-biases"]
  };

  const els = {
    tbody: document.getElementById("platforms-tbody"),
    count: document.getElementById("results-count"),
    compareGrid: document.getElementById("compare-grid"),
    compareStatus: document.getElementById("compare-status"),
    search: document.getElementById("search-input"),
    license: document.getElementById("license-select"),
    job: document.getElementById("job-select"),
    compliance: document.getElementById("compliance-select"),
    reset: document.getElementById("reset-filters"),
    chips: Array.from(document.querySelectorAll(".chip[data-cap]"))
  };

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function capMark(val) {
    return val
      ? '<span class="measured cap-yes">Yes</span>'
      : '<span class="measured cap-no">No</span>';
  }

  function matchesFilters(tool) {
    if (state.license !== "all" && tool.license_type !== state.license) return false;
    if (state.job !== "all" && !tool.jobs.includes(state.job)) return false;
    if (state.compliance !== "all" && !tool.compliance.includes(state.compliance)) return false;

    for (const cap of state.caps) {
      if (!tool.capabilities[cap]) return false;
    }

    if (state.search.trim()) {
      const q = state.search.trim().toLowerCase();
      const hay = `${tool.name} ${tool.tagline} ${tool.best_for} ${tool.license_name}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }

    return true;
  }

  function renderTable() {
    const filtered = state.tools.filter(matchesFilters);
    els.count.textContent = String(filtered.length);

    if (!filtered.length) {
      els.tbody.innerHTML = '<tr><td colspan="9">No MLOps platforms match the active filters. Try resetting one constraint.</td></tr>';
      return;
    }

    els.tbody.innerHTML = filtered
      .map((t) => {
        const isCompared = state.compare.includes(t.id);
        const licClass = t.license_type === "open-source" ? "tag--oss" : "tag--comm";
        const c = t.capabilities;
        return `
          <tr>
            <td>
              <span class="tool-name">${escapeHtml(t.name)}</span>
              <p class="tool-tagline">${escapeHtml(t.tagline)}</p>
            </td>
            <td><span class="tag ${licClass}">${escapeHtml(t.license_name)}</span></td>
            <td>${capMark(c.experiment_tracking)}</td>
            <td>${capMark(c.pipeline_orchestration)}</td>
            <td>${capMark(c.model_serving)}</td>
            <td>${capMark(c.kubernetes_native)}</td>
            <td>${capMark(c.llmops_support)}</td>
            <td class="measured">${escapeHtml(t.pricing)}</td>
            <td>
              <div class="row-actions">
                <a class="text-link" href="${escapeHtml(t.website)}" target="_blank" rel="noopener noreferrer">Website</a>
                ${t.github ? `<a class="text-link" href="${escapeHtml(t.github)}" target="_blank" rel="noopener noreferrer">GitHub</a>` : ""}
                <button type="button" class="btn compare-btn" data-compare="${escapeHtml(t.id)}" aria-pressed="${isCompared ? "true" : "false"}">
                  ${isCompared ? "Comparing" : "Compare"}
                </button>
              </div>
            </td>
          </tr>
        `;
      })
      .join("");
  }

  function renderCompare() {
    const selected = state.compare
      .map((id) => state.tools.find((t) => t.id === id))
      .filter(Boolean);

    els.compareStatus.textContent = `${selected.length} / 3 platforms selected for side-by-side diff`;

    if (!selected.length) {
      els.compareGrid.innerHTML = '<div class="compare-col"><p class="tool-tagline">Select up to 3 platforms from the table above to compare them side by side.</p></div>';
      return;
    }

    els.compareGrid.innerHTML = selected
      .map((t) => {
        const c = t.capabilities;
        return `
          <article class="compare-col">
            <h3>${escapeHtml(t.name)}</h3>
            <p class="tool-tagline">${escapeHtml(t.best_for)}</p>
            <ul class="compare-list">
              <li><span>License</span><span class="measured">${escapeHtml(t.license_name)}</span></li>
              <li><span>Pricing</span><span class="measured">${escapeHtml(t.pricing)}</span></li>
              <li><span>Tracking</span>${capMark(c.experiment_tracking)}</li>
              <li><span>Pipelines</span>${capMark(c.pipeline_orchestration)}</li>
              <li><span>Model registry</span>${capMark(c.model_registry)}</li>
              <li><span>Model serving</span>${capMark(c.model_serving)}</li>
              <li><span>Feature store</span>${capMark(c.feature_store)}</li>
              <li><span>Data versioning</span>${capMark(c.data_versioning)}</li>
              <li><span>Kubernetes</span>${capMark(c.kubernetes_native)}</li>
              <li><span>LLMOps</span>${capMark(c.llmops_support)}</li>
              <li><span>Compliance</span><span class="measured">${escapeHtml(t.compliance.join(", ") || "None listed")}</span></li>
            </ul>
          </article>
        `;
      })
      .join("");
  }

  function toggleCompare(id) {
    const idx = state.compare.indexOf(id);
    if (idx >= 0) {
      state.compare.splice(idx, 1);
    } else {
      if (state.compare.length >= 3) {
        state.compare.shift();
      }
      state.compare.push(id);
    }
    renderTable();
    renderCompare();
  }

  function bindEvents() {
    els.search.addEventListener("input", (e) => {
      state.search = e.target.value;
      renderTable();
    });

    els.license.addEventListener("change", (e) => {
      state.license = e.target.value;
      renderTable();
    });

    els.job.addEventListener("change", (e) => {
      state.job = e.target.value;
      renderTable();
    });

    els.compliance.addEventListener("change", (e) => {
      state.compliance = e.target.value;
      renderTable();
    });

    els.chips.forEach((chip) => {
      chip.addEventListener("click", () => {
        const cap = chip.dataset.cap;
        const next = !state.caps.has(cap);
        if (next) state.caps.add(cap);
        else state.caps.delete(cap);
        chip.setAttribute("aria-pressed", next ? "true" : "false");
        renderTable();
      });
    });

    els.reset.addEventListener("click", () => {
      state.search = "";
      state.license = "all";
      state.job = "all";
      state.compliance = "all";
      state.caps.clear();
      els.search.value = "";
      els.license.value = "all";
      els.job.value = "all";
      els.compliance.value = "all";
      els.chips.forEach((chip) => chip.setAttribute("aria-pressed", "false"));
      renderTable();
    });

    els.tbody.addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-compare]");
      if (btn) {
        toggleCompare(btn.dataset.compare);
      }
    });
  }

  async function init() {
    try {
      const res = await fetch("./tools.json");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      state.tools = data.tools || [];

      document.getElementById("stat-total").textContent = String(state.tools.length);
      document.getElementById("stat-oss").textContent = String(
        state.tools.filter((t) => t.license_type === "open-source").length
      );
      document.getElementById("stat-k8s").textContent = String(
        state.tools.filter((t) => t.capabilities.kubernetes_native).length
      );
      document.getElementById("stat-llm").textContent = String(
        state.tools.filter((t) => t.capabilities.llmops_support).length
      );

      bindEvents();
      renderTable();
      renderCompare();
    } catch (err) {
      els.tbody.innerHTML = `<tr><td colspan="9">Unable to load tools.json (${escapeHtml(err.message)}). Serve docs/ over HTTP or open via GitHub Pages.</td></tr>`;
    }
  }

  init();
})();
