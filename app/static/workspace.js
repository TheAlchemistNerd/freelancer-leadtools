"use strict";

const signin = document.querySelector("#workspace-signin");
const privateArea = document.querySelector("#workspace-private");
const status = document.querySelector("#workspace-page-status");
const proposals = document.querySelector("#proposal-list");
const documentStatus = document.querySelector("#document-status");
const documentList = document.querySelector("#document-list");
const review = document.querySelector("#draft-review");
let selectedDraft = null;
let sessionGeneration = 0;

async function requestWorkspace(path, method = "GET", body) {
  const response = await fetch("/workspace/" + path, {
    method,
    headers: {"Content-Type": "application/json"},
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
    signal: AbortSignal.timeout(20000),
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(typeof data.detail === "string" ? data.detail : "Please retry.");
    error.status = response.status;
    throw error;
  }
  return data;
}

function showSignedOut(message) {
  sessionGeneration += 1;
  selectedDraft = null;
  signin.hidden = false;
  privateArea.hidden = true;
  proposals.replaceChildren();
  documentList.replaceChildren();
  review.hidden = true;
  documentStatus.textContent = "";
  status.textContent = message;
}

async function refreshDocuments() {
  const result = await requestWorkspace("documents/jobs");
  if (!Array.isArray(result.items)) throw new Error("Invalid document list.");
  documentList.replaceChildren();
  for (const item of result.items) {
    const row = document.createElement("li");
    const kind = item.kind === "draft" ? "AI draft" : "Document";
    row.append(document.createTextNode(`${kind} · ${item.format} · ${item.status} `));
    if (item.kind === "render" && item.status === "completed") {
      const link = document.createElement("a");
      link.href = `/workspace/documents/jobs/${encodeURIComponent(item.id)}/download`;
      link.textContent = "Download";
      row.append(link);
    } else if (item.kind === "draft" && item.status === "completed") {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = "Review draft";
      button.addEventListener("click", () => loadDraft(item.id));
      row.append(button);
    }
    documentList.append(row);
  }
  if (!result.items.length) {
    const row = document.createElement("li");
    row.textContent = "No documents yet.";
    documentList.append(row);
  }
}

async function loadDraft(id) {
  try {
    const result = await requestWorkspace(`documents/drafts/${encodeURIComponent(id)}`);
    if (result.status !== "completed" || !result.draft || !result.sha256) {
      documentStatus.textContent = `AI draft status: ${result.status}.`;
      return;
    }
    const draft = result.draft;
    const missing = Array.isArray(draft.missing_information)
      ? draft.missing_information : [];
    const content = document.querySelector("#draft-content");
    content.replaceChildren();
    const reviewSections = Array.isArray(result.review_sections)
      ? result.review_sections : draft.sections;
    if (Array.isArray(reviewSections)) {
      for (const section of reviewSections) {
        if (typeof section.heading !== "string" || typeof section.body !== "string") {
          throw new Error("The draft contains an invalid section.");
        }
        const item = document.createElement("section");
        item.className = "draft-section";
        const heading = document.createElement("h4");
        heading.textContent = section.heading;
        const body = document.createElement("p");
        body.textContent = section.body;
        item.append(heading, body);
        content.append(item);
      }
    } else if (typeof draft.summary === "string") {
      const item = document.createElement("section");
      item.className = "draft-section";
      const heading = document.createElement("h4");
      heading.textContent = "Introduction";
      const body = document.createElement("p");
      body.textContent = draft.summary;
      item.append(heading, body);
      content.append(item);
    } else {
      throw new Error("The draft has no reviewable content.");
    }
    selectedDraft = {id, sha256: result.sha256, missing: missing.length};
    const list = document.querySelector("#draft-missing");
    list.replaceChildren();
    for (const flag of missing) {
      const row = document.createElement("li");
      row.textContent = flag;
      list.append(row);
    }
    document.querySelector("#draft-acknowledge-row").hidden = missing.length === 0;
    document.querySelector("#draft-acknowledge").checked = false;
    review.hidden = false;
    documentStatus.textContent = "Review this exact AI draft before accepting it.";
  } catch (error) {
    if (error.status === 401) showSignedOut("Session expired. Sign in again.");
    else documentStatus.textContent = error.message;
  }
}

async function watchJob(id, kind) {
  const generation = sessionGeneration;
  for (let attempt = 0; attempt < 60 && generation === sessionGeneration; attempt += 1) {
    await new Promise(resolve => setTimeout(resolve, 2000));
    if (generation !== sessionGeneration) return;
    try {
      const path = kind === "draft" ? `documents/drafts/${id}` : `documents/jobs/${id}`;
      const job = await requestWorkspace(path);
      if (["completed", "failed", "cancelled", "deleted"].includes(job.status)) {
        await refreshDocuments();
        if (kind === "draft" && job.status === "completed") await loadDraft(id);
        else if (
          kind === "draft" &&
          job.status === "failed" &&
          job.error_code === "payment_required"
        ) {
          documentStatus.textContent = "OpenRouter requires available credits or a higher spend limit. Check its billing settings before submitting another AI draft.";
        } else documentStatus.textContent = `Document job ${job.status}.`;
        return;
      }
    } catch (error) {
      if (error.status === 401) showSignedOut("Session expired. Sign in again.");
      else documentStatus.textContent = error.message;
      return;
    }
  }
  if (generation === sessionGeneration) {
    documentStatus.textContent = "Still processing. This job remains in your list; check it again later.";
    await refreshDocuments();
  }
}

async function refreshProposals() {
  try {
    const result = await requestWorkspace("proposals");
    if (!Array.isArray(result.items)) throw new Error("Invalid proposal list.");
    proposals.replaceChildren();
    for (const item of result.items) {
      const row = document.createElement("li");
      row.textContent = `${item.title} · ${item.client_name} · ${item.status}`;
      proposals.append(row);
    }
    signin.hidden = true;
    privateArea.hidden = false;
    status.textContent = result.items.length
      ? `Showing ${result.items.length} proposal draft(s).`
      : "No proposal drafts yet.";
    await refreshDocuments();
  } catch (error) {
    if (error.status === 401) showSignedOut("Sign in to view your private workspace.");
    else status.textContent = error.message;
  }
}

document.querySelector("#workspace-auth-form").addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector("button[type=submit]");
  const password = form.querySelector("#workspace-password");
  button.disabled = true;
  try {
    await requestWorkspace("login", "POST", {
      email: form.querySelector("#workspace-email").value,
      password: password.value,
    });
    await refreshProposals();
  } catch (error) {
    showSignedOut(error.message);
  } finally {
    password.value = "";
    button.disabled = false;
  }
});

document.querySelector("#document-ai").addEventListener("change", event => {
  const enabled = event.currentTarget.checked;
  document.querySelector("#document-ai-fields").hidden = !enabled;
  document.querySelector("#document-brief").required = enabled;
  document.querySelector("#document-consent").required = enabled;
});

document.querySelector("#document-form").addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector("button[type=submit]");
  button.disabled = true;
  documentStatus.textContent = "Submitting your document job…";
  const documentPayload = {
    request_id: crypto.randomUUID(),
    template: form.querySelector("#document-template").value,
    format: form.querySelector("#document-format").value,
    title: form.querySelector("#document-title").value,
    client_name: form.querySelector("#document-client").value,
    author_name: form.querySelector("#document-author").value,
    sections: [{heading: "Scope and terms", body: form.querySelector("#document-body").value}],
  };
  try {
    const useAI = form.querySelector("#document-ai").checked;
    const path = useAI ? "documents/drafts" : "documents/jobs";
    const body = useAI
      ? {document: documentPayload, brief: form.querySelector("#document-brief").value,
         consent_to_provider: form.querySelector("#document-consent").checked}
      : documentPayload;
    const job = await requestWorkspace(path, "POST", body);
    form.reset();
    document.querySelector("#document-ai-fields").hidden = true;
    review.hidden = true;
    selectedDraft = null;
    documentStatus.textContent = useAI
      ? "OpenRouter draft queued. Review it before any file is rendered."
      : "Document rendering queued. Nothing was sent or signed.";
    await refreshDocuments();
    void watchJob(job.id, useAI ? "draft" : "render");
  } catch (error) {
    if (error.status === 401) showSignedOut("Session expired. Sign in again.");
    else documentStatus.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

document.querySelector("#draft-accept").addEventListener("click", async event => {
  if (!selectedDraft) return;
  if (selectedDraft.missing && !document.querySelector("#draft-acknowledge").checked) {
    documentStatus.textContent = "Review and acknowledge the missing information first.";
    return;
  }
  const button = event.currentTarget;
  button.disabled = true;
  try {
    const result = await requestWorkspace(
      `documents/drafts/${selectedDraft.id}/accept`, "POST",
      {sha256: selectedDraft.sha256,
       acknowledge_missing_information: Boolean(document.querySelector("#draft-acknowledge").checked)},
    );
    review.hidden = true;
    selectedDraft = null;
    documentStatus.textContent = "Accepted version frozen. Rendering a file; nothing was sent or signed.";
    await refreshDocuments();
    void watchJob(result.id, "render");
  } catch (error) {
    if (error.status === 401) showSignedOut("Session expired. Sign in again.");
    else documentStatus.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

document.querySelector("#proposal-form").addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector("button[type=submit]");
  button.disabled = true;
  status.textContent = "Saving proposal draft…";
  try {
    await requestWorkspace("proposals", "POST", {
      title: form.querySelector("#proposal-title").value,
      client_name: form.querySelector("#proposal-client").value,
      client_email: form.querySelector("#proposal-email").value,
      summary: form.querySelector("#proposal-summary").value,
    });
    form.reset();
    await refreshProposals();
    status.textContent = "Proposal draft saved. Nothing was sent or signed.";
  } catch (error) {
    if (error.status === 401) showSignedOut("Session expired. Sign in again.");
    else status.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

document.querySelector("#workspace-signout").addEventListener("click", async () => {
  try {
    await requestWorkspace("logout", "POST", {});
    showSignedOut("Signed out.");
  } catch (error) {
    status.textContent = error.message;
  }
});

refreshProposals();
