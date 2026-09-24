"use strict";

const signin = document.querySelector("#workspace-signin");
const privateArea = document.querySelector("#workspace-private");
const status = document.querySelector("#workspace-page-status");
const proposals = document.querySelector("#proposal-list");

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
  signin.hidden = false;
  privateArea.hidden = true;
  proposals.replaceChildren();
  status.textContent = message;
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
