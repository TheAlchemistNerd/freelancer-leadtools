const form = document.querySelector("form[data-tool]");
if (form) {
  const status = document.querySelector("#status");
  const result = document.querySelector("#result");
  const download = document.querySelector("#download");
  let artifact = null;
  let generation = 0;
  const save = document.createElement("button");
  save.type = "button"; save.textContent = "Save to DealFlow"; save.hidden = true;
  download.after(save);
  const account = document.createElement("section");
  account.hidden = true;
  account.innerHTML = `<h3>Save this result</h3>
    <p>Sign in or create an account. Your calculation stays on this page. New passwords need at least 12 characters.</p>
    <form id="workspace-login"><label for="workspace-email">Email</label>
    <input id="workspace-email" type="email" autocomplete="username" required>
    <label for="workspace-password">Password</label>
    <input id="workspace-password" type="password" autocomplete="current-password" required>
    <button type="submit" value="login">Sign in</button>
    <button type="submit" value="register">Create account</button></form>
    <label><input id="save-consent" type="checkbox"> Save these inputs and this result in my private DealFlow workspace.</label>
    <button id="confirm-save" type="button">Confirm save</button>
    <button id="workspace-logout" type="button">Sign out</button>
    <button id="workspace-list" type="button">View saved results</button>
    <section id="saved-results" aria-label="Saved results"></section>
    <button id="workspace-more" type="button" hidden>More saved results</button>
    <p id="workspace-status" role="status" aria-live="polite"></p>
    <p><a href="/workspace">Open your proposal workspace →</a></p>`;
  save.after(account);
  const openWorkspace = document.createElement("button");
  openWorkspace.type = "button"; openWorkspace.textContent = "Sign in to your workspace";
  openWorkspace.hidden = form.dataset.tool === "skill-gap";
  account.before(openWorkspace);
  openWorkspace.addEventListener("click", () => { account.hidden = false; });
  const workspaceStatus = account.querySelector("#workspace-status");
  const savedResults = account.querySelector("#saved-results");
  const more = account.querySelector("#workspace-more");
  let accountVersion = 0;
  let offset = 0;
  const clearSaved = () => {
    accountVersion++; offset = 0; savedResults.replaceChildren(); more.hidden = true;
  };
  let saveId = null;
  let saving = false;
  const invalidateSave = () => {
    save.hidden = true; saveId = null; account.hidden = true;
    account.querySelector("#save-consent").checked = false;
  };
  async function workspace(path, payload, method = "POST") {
    const response = await fetch("/workspace/" + path, {
      method, headers: {"Content-Type": "application/json"}, cache: "no-store",
      body: method === "GET" ? undefined : JSON.stringify(payload), signal: AbortSignal.timeout(20000)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Check your details and retry.");
    return data;
  }
  save.addEventListener("click", () => { account.hidden = false; });
  account.querySelector("form").addEventListener("submit", async event => {
    event.preventDefault();
    const password = account.querySelector("#workspace-password");
    const buttons = [...event.currentTarget.querySelectorAll("button")];
    const action = event.submitter?.value || "login";
    if (action === "register" && password.value.length < 12) {
      workspaceStatus.textContent = "Use at least 12 characters for a new password."; return;
    }
    buttons.forEach(button => { button.disabled = true; });
    clearSaved();
    try {
      await workspace(action, {email: account.querySelector("#workspace-email").value, password: password.value});
      workspaceStatus.textContent = action === "register"
        ? "Account created. Enter your password again and sign in to save your result."
        : "Signed in. Review the result, check the confirmation and save.";
    } catch (error) { workspaceStatus.textContent = error.message; }
    finally { password.value = ""; buttons.forEach(button => { button.disabled = false; }); }
  });
  account.querySelector("#confirm-save").addEventListener("click", async () => {
    if (!artifact || saving) return;
    if (!account.querySelector("#save-consent").checked) {
      workspaceStatus.textContent = "Confirm that you want to save these inputs and this result."; return;
    }
    saveId ||= crypto.randomUUID();
    const version = generation;
    const payload = {...artifact, request_id: saveId, confirmed: true, schema_version: 1};
    saving = true; workspaceStatus.textContent = "Saving…";
    try {
      const saved = await workspace("tool-results", payload);
      if (version === generation) workspaceStatus.textContent = "Saved to your private workspace. Reference: " + saved.id;
    } catch (error) { if (version === generation) workspaceStatus.textContent = error.message; }
    finally { saving = false; }
  });
  account.querySelector("#workspace-logout").addEventListener("click", async () => {
    clearSaved();
    try { await workspace("logout", {}); workspaceStatus.textContent = "Signed out. Your calculation is still here."; }
    catch (error) { workspaceStatus.textContent = error.message; }
  });
  async function listSaved(reset) {
    if (reset) clearSaved();
    const version = accountVersion;
    more.disabled = true;
    try {
      const body = await workspace("tool-results?offset=" + offset, undefined, "GET");
      if (version !== accountVersion) return;
      if (!Array.isArray(body.items)) throw new Error("Invalid saved-results response.");
      for (const item of body.items) {
        const details = document.createElement("details");
        const summary = document.createElement("summary");
        summary.textContent = (item.snapshot?.tool || "Saved result") + " · " + item.created_at;
        const note = document.createElement("p");
        note.textContent = "Saved planning snapshot—not a verified quote or approved contract.";
        const content = document.createElement("pre");
        content.style.whiteSpace = "pre-wrap"; content.style.overflowWrap = "anywhere";
        content.textContent = JSON.stringify(item.snapshot, null, 2);
        details.append(summary, note, content); savedResults.append(details);
      }
      offset += body.items.length; more.hidden = body.items.length < 20;
      workspaceStatus.textContent = offset ? "Showing " + offset + " saved results." : "No saved results yet.";
    } catch (error) {
      if (version === accountVersion) { clearSaved(); workspaceStatus.textContent = error.message; }
    } finally { more.disabled = false; }
  }
  account.querySelector("#workspace-list").addEventListener("click", () => { listSaved(true); });
  more.addEventListener("click", () => { listSaved(false); });
  form.addEventListener("input", () => {
    generation++;
    invalidateSave();
    artifact = null; result.replaceChildren(); download.hidden = true;
    document.querySelector("#empty").hidden = false;
    status.textContent = "Inputs changed. Calculate again to update the result.";
  });
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const version = ++generation;
    invalidateSave();
    const inputs = {};
    for (const input of form.querySelectorAll("input")) {
      if (!input.value && !input.required) continue;
      inputs[input.name] = input.dataset.kind === "array"
        ? input.value.split(",").map(x => x.trim()).filter(Boolean)
        : ["integer", "number"].includes(input.dataset.kind) ? Number(input.value) : input.value;
    }
    artifact = null; download.hidden = true; result.replaceChildren();
    status.textContent = "Calculating…";
    const submit = form.querySelector("button[type=submit]");
    submit.disabled = true;
    try {
      const response = await fetch("/calculators/" + form.dataset.tool, {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify(inputs), signal: AbortSignal.timeout(15000)
      });
      const body = await response.json();
      if (version !== generation) return;
      if (!response.ok) throw new Error(Array.isArray(body.detail)
        ? body.detail.map(x => x.loc.slice(1).join(".") + ": " + x.msg).join("; ")
        : "Unable to calculate. Check your inputs and try again.");
      const list = document.createElement("dl");
      for (const [key, value] of Object.entries(body)) {
        if (key === "cta") continue; // No unimplemented signup/handoff promises.
        const term = document.createElement("dt"); term.textContent = key.replaceAll("_", " ");
        const detail = document.createElement("dd");
        if (Array.isArray(value)) {
          const items = document.createElement("ul");
          for (const item of value) {
            const li = document.createElement("li");
            li.textContent = typeof item === "object" ? JSON.stringify(item) : String(item);
            items.append(li);
          }
          detail.append(items);
        } else {
          detail.textContent = value === null ? "Not supplied / not measured"
            : typeof value === "object" ? JSON.stringify(value, null, 2) : String(value);
        }
        if (key === "estimate" || key === "hourly_rate") detail.className = "primary-result";
        list.append(term, detail);
      }
      result.replaceChildren(list); document.querySelector("#empty").hidden = true;
      artifact = {tool: form.dataset.tool, inputs, result: body};
      save.hidden = form.dataset.tool === "skill-gap";
      download.hidden = false; status.textContent = "Result ready.";
    } catch (error) {
      if (version === generation) status.textContent = error.message || "Connection failed. Try again.";
    } finally { submit.disabled = false; }
  });
  download.addEventListener("click", () => {
    if (!artifact) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(artifact, null, 2)], {type:"application/json"}));
    const link = document.createElement("a"); link.href = url;
    link.download = form.dataset.tool + "-result.json"; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
}
