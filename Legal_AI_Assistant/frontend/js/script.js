
    // All backend routes start with /api (see main.py)
    const API = "/api";
    const chatHistory = [];

    const fileInput = document.getElementById("pdfFile");
    const drop = document.getElementById("drop");
    const fileName = document.getElementById("fileName");
    const uploadBtn = document.getElementById("uploadBtn");
    const statusEl = document.getElementById("status");
    const messages = document.getElementById("messages");
    const askForm = document.getElementById("askForm");
    const questionInput = document.getElementById("question");
    const askBtn = document.getElementById("askBtn");
    const chips = document.getElementById("chips");


    /* ---------- choose / drag a file ---------- */
    fileInput.addEventListener("change", showFileName);

    drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
    drop.addEventListener("dragleave", () => drop.classList.remove("over"));
    drop.addEventListener("drop", (e) => {
      e.preventDefault();
      drop.classList.remove("over");
      fileInput.files = e.dataTransfer.files;
      showFileName();
    });

    function showFileName() {
      const file = fileInput.files[0];
      if (file) {
        fileName.textContent = file.name;
        fileName.hidden = false;
      }
    }

    function setStatus(text, type = "") {
      statusEl.textContent = text;
      statusEl.className = "status " + type;
    }


    /* ---------- upload PDF  ->  POST /api/upload ---------- */
    uploadBtn.addEventListener("click", async () => {
      const file = fileInput.files[0];
      if (!file) { setStatus("Choose a PDF first.", "err"); return; }

      const formData = new FormData();
      formData.append("file", file);            // "file" matches main.py

      uploadBtn.disabled = true;
      setStatus("Reading and indexing your document...");

      try {
        const res = await fetch(API + "/upload", { method: "POST", body: formData });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Upload failed.");

        setStatus("Ready: " + data.chunks + " sections indexed.", "ok");
        questionInput.disabled = false;
        askBtn.disabled = false;
        questionInput.placeholder = "Ask something about your contract...";
        addMessage("bot", "Done! I've read " + data.filename + ". What would you like to know?");
      } catch (e) {
        setStatus(e.message || "Upload failed. Check the server terminal.", "err");
      }
      uploadBtn.disabled = false;
    });


    /* ---------- ask a question  ->  POST /api/ask ---------- */
    askForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const question = questionInput.value.trim();
      if (!question) return;

      addMessage("user", question);
      questionInput.value = "";

      const loading = addMessage("bot", "");
      loading.querySelector(".bubble").innerHTML = "<span class='dots'><span></span><span></span><span></span></span>";

      try {
        const res = await fetch(API + "/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: question, history: chatHistory.slice(-10) })     // "question" matches main.py
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Upload failed.");

        loading.querySelector(".bubble").textContent = data.answer;
        addSources(loading, data.chunks);
      } catch (e) {
        loading.querySelector(".bubble").textContent =
          e.message || "Something went wrong. Check the server terminal.";
      }
      scrollDown();
    });


    /* ---------- suggestion chips ---------- */
    chips.addEventListener("click", (e) => {
      if (e.target.tagName !== "BUTTON" || questionInput.disabled) return;
      questionInput.value = e.target.textContent;
      askForm.requestSubmit();
    });


    /* ---------- helpers ---------- */
    function addMessage(who, text) {
      const msg = document.createElement("div");
      msg.className = "msg " + who;

      const bubble = document.createElement("div");
      bubble.className = "bubble";
      bubble.textContent = text;

      msg.appendChild(bubble);
      messages.appendChild(msg);
      scrollDown();
      return msg;
    }

    function addSources(msg, chunks) {
      if (!chunks || chunks.length === 0) return;

      const details = document.createElement("details");
      const summary = document.createElement("summary");
      summary.textContent = "View sources (" + chunks.length + ")";
      details.appendChild(summary);

      chunks.forEach((c) => {
        const div = document.createElement("div");
        div.className = "chunk";
        div.textContent = c;
        details.appendChild(div);
      });
      msg.appendChild(details);
    }

    function scrollDown() {
      messages.scrollTop = messages.scrollHeight;
    }

    // ---------- upcoming functionality ----------
    // Add new features' JS below (clause lookup, summary, flags, comparison)
  