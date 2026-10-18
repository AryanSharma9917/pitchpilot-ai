const form = document.querySelector("#brief-form");
const modeButtons = [...document.querySelectorAll("[data-mode]")];
const generateButton = document.querySelector("#generate-button");
const generateLabel = document.querySelector("#generate-label");
const outputEmpty = document.querySelector("#output-empty");
const loadingState = document.querySelector("#loading-state");
const errorState = document.querySelector("#error-state");
const resultArea = document.querySelector("#result-area");
const preview = document.querySelector("#proposal-preview");
const appMessage = document.querySelector("#app-message");
const budgetType = document.querySelector("#budget-type");
const budgetAmount = document.querySelector("#budget-amount");
let selectedMode = "proposal";
let isGenerating = false;
let loadingTimer;
let currentObjectUrl;
let lastMode = null;

const modeLabels = { proposal: "Full proposal", quote: "Quick quote", email: "Client email" };
const loadingMessages = ["Reading the client brief…", "Structuring the scope…", "Preparing your draft…"];

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function editable(node, label) {
  node.dataset.editable = "true";
  node.dataset.label = label;
  node.contentEditable = "false";
  node.setAttribute("aria-label", `${label}; use Edit to make changes`);
  return node;
}

function addParagraph(container, text, label) {
  container.append(editable(element("p", text), label));
}

function addSection(container, title, values, label) {
  container.append(element("h3", title));
  if (Array.isArray(values)) {
    const list = element("ul");
    values.forEach((value, index) => list.append(editable(element("li", value), `${label} ${index + 1}`)));
    container.append(list);
  } else {
    addParagraph(container, values, label);
  }
}

function addPricingTable(container, rows) {
  container.append(element("h3", "Pricing"));
  const table = element("table");
  const head = element("thead");
  const headerRow = element("tr");
  ["Item", "Details", "Amount"].forEach((label) => headerRow.append(element("th", label)));
  head.append(headerRow);
  const body = element("tbody");
  rows.forEach((row, index) => {
    const tr = element("tr");
    [row.item, row.details || "", row.amount].forEach((text, cellIndex) => {
      const cell = element("td", text);
      editable(cell, `Pricing item ${index + 1}, ${["name", "details", "amount"][cellIndex]}`);
      tr.append(cell);
    });
    body.append(tr);
  });
  table.append(head, body);
  container.append(table);
}

function buildProposal(data) {
  const title = editable(element("h2", data.title), "Proposal title");
  preview.append(title);
  addParagraph(preview, data.executive_summary, "Executive summary");
  addSection(preview, "Understanding your needs", data.client_needs, "Client need");
  addSection(preview, "Proposed solution", data.proposed_solution, "Proposed solution");
  addSection(preview, "Scope of work", data.scope, "Scope item");
  addSection(preview, "Deliverables", data.deliverables, "Deliverable");
  preview.append(element("h3", "Timeline & milestones"));
  const milestones = element("ul");
  data.milestones.forEach((item, index) => {
    const li = element("li");
    li.append(editable(element("strong", `${item.name} — ${item.duration}`), `Milestone ${index + 1}`));
    if (item.description) li.append(document.createTextNode(`: ${item.description}`));
    milestones.append(li);
  });
  preview.append(milestones);
  addPricingTable(preview, data.pricing);
  addSection(preview, "Assumptions", data.assumptions, "Assumption");
  addSection(preview, "Out of scope", data.out_of_scope, "Out-of-scope item");
  addSection(preview, "Terms & notes", data.terms, "Terms and notes");
  addSection(preview, "Next steps", data.next_steps, "Next steps");
}

function buildQuote(data) {
  preview.append(editable(element("h2", "Quick project estimate"), "Quote title"));
  addParagraph(preview, data.project_summary, "Project summary");
  addSection(preview, "Deliverables", data.deliverables, "Deliverable");
  addSection(preview, "Estimated timeline", data.timeline, "Estimated timeline");
  addPricingTable(preview, data.pricing);
  const total = element("div", null, "total-line");
  total.append(editable(element("span", "Total estimate"), "Total label"));
  total.append(editable(element("span", data.total_estimate), "Total estimate amount"));
  preview.append(total);
  addSection(preview, "Assumptions", data.assumptions, "Assumption");
}

function buildEmail(data) {
  const card = element("div", null, "email-copy");
  card.append(editable(element("p", `Subject: ${data.subject}`, "email-subject"), "Email subject"));
  addParagraph(card, data.greeting, "Email greeting");
  addParagraph(card, data.body, "Email body");
  addParagraph(card, data.closing, "Email closing");
  addParagraph(card, data.signature, "Email signature");
  preview.append(card);
}

function showError(message) {
  errorState.hidden = false;
  document.querySelector("#error-message").textContent = message;
}

function statusMessage(message) {
  appMessage.textContent = message;
  window.setTimeout(() => {
    if (appMessage.textContent === message) appMessage.textContent = "";
  }, 3000);
}

function setBusy(busy) {
  isGenerating = busy;
  generateButton.disabled = busy;
  generateLabel.textContent = busy ? "Generating…" : `Generate ${modeLabels[selectedMode].toLowerCase()}`;
  modeButtons.forEach((button) => { button.disabled = busy; });
  document.querySelector("#regenerate-button").disabled = busy;
  document.querySelector("#new-button").disabled = busy;
  document.querySelector("#loading-message").textContent = loadingMessages[0];
  if (busy) {
    let messageIndex = 0;
    loadingTimer = window.setInterval(() => {
      messageIndex = (messageIndex + 1) % loadingMessages.length;
      document.querySelector("#loading-message").textContent = loadingMessages[messageIndex];
    }, 3800);
  } else {
    window.clearInterval(loadingTimer);
  }
}

function requestData() {
  const data = Object.fromEntries(new FormData(form).entries());
  if (data.budget_type === "unknown") data.budget_amount = null;
  return data;
}

async function generate() {
  if (isGenerating || !form.reportValidity()) return;
  errorState.hidden = true;
  resultArea.hidden = true;
  outputEmpty.hidden = true;
  loadingState.hidden = false;
  setBusy(true);
  try {
    const response = await fetch(`/api/generate/${selectedMode}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestData()),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || "The server could not generate a draft.");
    preview.replaceChildren();
    if (selectedMode === "proposal") buildProposal(payload);
    if (selectedMode === "quote") buildQuote(payload);
    if (selectedMode === "email") buildEmail(payload);
    lastMode = selectedMode;
    document.querySelector("#result-mode-label").textContent = modeLabels[selectedMode];
    document.querySelector("#edit-button").textContent = "Edit";
    document.querySelector("#edit-button").setAttribute("aria-pressed", "false");
    document.querySelector("#copy-button").disabled = selectedMode === "email";
    document.querySelector("#copy-email-button").disabled = selectedMode !== "email";
    resultArea.hidden = false;
  } catch (error) {
    showError(error instanceof TypeError
      ? "PitchPilot could not reach the backend. Check that the application server is running and try again."
      : error.message);
  } finally {
    loadingState.hidden = true;
    setBusy(false);
  }
}

function setEditing(enabled) {
  preview.querySelectorAll("[data-editable]").forEach((node) => {
    node.contentEditable = enabled ? "true" : "false";
    node.setAttribute("aria-label", enabled ? node.dataset.label : `${node.dataset.label}; use Edit to make changes`);
  });
  const button = document.querySelector("#edit-button");
  button.textContent = enabled ? "Done editing" : "Edit";
  button.setAttribute("aria-pressed", String(enabled));
}

function markdownFor(node) {
  if (node.nodeType === Node.TEXT_NODE) return node.textContent.trim();
  if (node.nodeType !== Node.ELEMENT_NODE) return "";
  const children = [...node.childNodes].map(markdownFor).filter(Boolean).join("");
  const text = node.textContent.trim();
  if (node.matches("h2")) return `# ${text}\n\n`;
  if (node.matches("h3")) return `## ${text}\n\n`;
  if (node.matches("li")) return `- ${children || text}\n`;
  if (node.matches("ul")) return `${children}\n`;
  if (node.matches("p")) return `${text}\n\n`;
  if (node.matches("table")) {
    const rows = [...node.querySelectorAll("tr")].map((row) =>
      `| ${[...row.children].map((cell) => cell.textContent.trim().replaceAll("|", "\\|")).join(" | ")} |`,
    );
    if (rows.length > 1) rows.splice(1, 0, `| ${[...node.querySelectorAll("th")].map(() => "---").join(" | ")} |`);
    return `${rows.join("\n")}\n\n`;
  }
  if (node.classList.contains("total-line")) return `**${text}**\n\n`;
  if (node.classList.contains("email-copy")) return `${children}`;
  if (node.matches("strong")) return `**${text}**`;
  return children;
}

function readableText() {
  return preview.innerText.trim();
}

async function copyText(text, label) {
  try {
    await navigator.clipboard.writeText(text);
    statusMessage(`${label} copied to clipboard.`);
  } catch {
    statusMessage("Clipboard access was blocked. Select and copy the draft manually.");
  }
}

function refreshModelStatus() {
  const status = document.querySelector("#model-status");
  const label = document.querySelector("#model-status-label");
  fetch("/api/model/status")
    .then((response) => {
      if (!response.ok) throw new Error("status unavailable");
      return response.json();
    })
    .then((data) => {
      document.querySelector("#model-name").textContent = data.model;
      status.className = "model-status";
      if (data.status === "ready") {
        status.classList.add("status-ready");
        label.textContent = `${data.model} ready`;
      } else if (data.status === "model_missing") {
        status.classList.add("status-missing");
        label.textContent = "Model not installed";
        status.title = `Pull the configured model (${data.model}) using Ollama.`;
      } else {
        status.classList.add("status-unavailable");
        label.textContent = "Ollama unavailable";
        status.title = "Start Ollama and confirm OLLAMA_BASE_URL.";
      }
    })
    .catch(() => {
      status.className = "model-status status-unavailable";
      label.textContent = "Backend unavailable";
      status.title = "Start the PitchPilot application server.";
    });
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  generate();
});

modeButtons.forEach((button) => button.addEventListener("click", () => {
  selectedMode = button.dataset.mode;
  modeButtons.forEach((option) => {
    const selected = option === button;
    option.classList.toggle("is-selected", selected);
    option.setAttribute("aria-pressed", String(selected));
  });
  generateLabel.textContent = `Generate ${modeLabels[selectedMode].toLowerCase()}`;
}));

budgetType.addEventListener("change", () => {
  const required = budgetType.value !== "unknown";
  budgetAmount.disabled = !required;
  budgetAmount.required = required;
  if (!required) budgetAmount.value = "";
});

document.querySelector("#load-demo-button").addEventListener("click", () => {
  const demo = {
    "client-name": "Northstar Accounting",
    "project-name": "Company Website Redesign",
    "project-type": "Web Development",
    timeline: "4–6 weeks",
    brief: "Redesign and build a modern five-page website for a small accounting firm. The site should include Home, About, Services, Resources, and Contact pages. It must work well on mobile devices, provide accessible navigation, include a contact form, and have basic SEO metadata. The client will supply the logo and final written content. Include deployment documentation and one revision round.",
    "budget-type": "unknown",
    currency: "USD",
    "freelancer-name": "Alex Morgan Studio",
    expertise: "Independent web developer specializing in responsive, accessible websites for small businesses",
    tone: "Professional",
    constraints: "Use the client’s existing hosting provider. Do not include ongoing maintenance, copywriting, or logo design.",
  };
  Object.entries(demo).forEach(([id, value]) => {
    document.getElementById(id).value = value;
  });
  budgetType.dispatchEvent(new Event("change"));
  document.querySelector("#brief").dispatchEvent(new Event("input"));
  statusMessage("Demo details loaded. Choose a mode and generate.");
});

document.querySelector("#brief").addEventListener("input", (event) => {
  document.querySelector("#brief-count").textContent = `${event.target.value.length.toLocaleString()} / 12,000`;
});

document.querySelector("#edit-button").addEventListener("click", (event) => {
  setEditing(event.currentTarget.getAttribute("aria-pressed") !== "true");
});
document.querySelector("#regenerate-button").addEventListener("click", generate);
document.querySelector("#new-button").addEventListener("click", () => {
  preview.replaceChildren();
  resultArea.hidden = true;
  errorState.hidden = true;
  outputEmpty.hidden = false;
  lastMode = null;
  appMessage.textContent = "";
});
document.querySelector("#copy-button").addEventListener("click", () => copyText(readableText(), "Draft"));
document.querySelector("#copy-email-button").addEventListener("click", () => copyText(readableText(), "Email"));
document.querySelector("#download-button").addEventListener("click", () => {
  if (currentObjectUrl) URL.revokeObjectURL(currentObjectUrl);
  const blob = new Blob([markdownFor(preview)], { type: "text/markdown;charset=utf-8" });
  currentObjectUrl = URL.createObjectURL(blob);
  const link = element("a");
  link.href = currentObjectUrl;
  link.download = `pitchpilot-${lastMode || "draft"}.md`;
  document.body.append(link);
  link.click();
  link.remove();
  statusMessage("Markdown draft downloaded.");
});
document.querySelector("#print-button").addEventListener("click", () => window.print());

const privacyDialog = document.querySelector("#privacy-dialog");
document.querySelector("#privacy-open").addEventListener("click", () => privacyDialog.showModal());
document.querySelector("#privacy-close").addEventListener("click", () => privacyDialog.close());
document.querySelector("#privacy-done").addEventListener("click", () => privacyDialog.close());
privacyDialog.addEventListener("click", (event) => {
  if (event.target === privacyDialog) privacyDialog.close();
});

refreshModelStatus();
window.setInterval(refreshModelStatus, 30000);
