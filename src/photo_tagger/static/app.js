let currentFolder = "";
let images = [];
let browsePath = "";

const folderInput = document.getElementById("folder-input");
const browseBtn = document.getElementById("browse-btn");
const loadBtn = document.getElementById("load-btn");
const tagAllBtn = document.getElementById("tag-all-btn");
const actionBar = document.getElementById("action-bar");
const imageGrid = document.getElementById("image-grid");
const progressBar = document.getElementById("progress-bar");
const progressText = document.getElementById("progress-text");

const browseModal = document.getElementById("browse-modal");
const browsePathEl = document.getElementById("browse-path");
const browseList = document.getElementById("browse-list");
const modalCloseBtn = document.getElementById("modal-close-btn");
const modalSelectBtn = document.getElementById("modal-select-btn");

browseBtn.addEventListener("click", openBrowser);
loadBtn.addEventListener("click", loadFolder);
folderInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") loadFolder();
});
tagAllBtn.addEventListener("click", tagAll);
modalCloseBtn.addEventListener("click", closeBrowser);
modalSelectBtn.addEventListener("click", selectFolder);
browseModal.addEventListener("click", (e) => {
    if (e.target === browseModal) closeBrowser();
});

async function openBrowser() {
    browseModal.style.display = "flex";
    const startPath = folderInput.value.trim() || "";
    await navigateTo(startPath);
}

function closeBrowser() {
    browseModal.style.display = "none";
}

function selectFolder() {
    if (browsePath) {
        folderInput.value = browsePath;
        closeBrowser();
        loadFolder();
    }
}

async function navigateTo(path) {
    const url = `/api/browse?path=${encodeURIComponent(path)}`;
    const resp = await fetch(url);
    const data = await resp.json();

    if (data.error) {
        return;
    }

    browsePath = data.current;
    browsePathEl.textContent = data.current;

    browseList.innerHTML = "";

    if (data.parent) {
        const li = document.createElement("li");
        li.textContent = "\u2190 ..";
        li.className = "browse-item browse-parent";
        li.addEventListener("click", () => navigateTo(data.parent));
        browseList.appendChild(li);
    }

    for (const dir of data.dirs) {
        const li = document.createElement("li");
        li.textContent = dir;
        li.className = "browse-item";
        li.addEventListener("click", () => navigateTo(browsePath + "/" + dir));
        browseList.appendChild(li);
    }
}

async function loadFolder() {
    const folder = folderInput.value.trim();
    if (!folder) return;

    currentFolder = folder;
    loadBtn.disabled = true;
    loadBtn.textContent = "Loading\u2026";

    try {
        const resp = await fetch(`/api/images?folder=${encodeURIComponent(folder)}`);
        const data = await resp.json();

        if (data.error) {
            imageGrid.innerHTML = `<p class="error">${data.error}</p>`;
            actionBar.style.display = "none";
            return;
        }

        images = data.images;
        renderGrid();
        actionBar.style.display = "flex";
        progressText.textContent = `${images.length} images found`;
        progressBar.style.display = "none";
    } finally {
        loadBtn.disabled = false;
        loadBtn.textContent = "Load";
    }
}

function renderGrid() {
    imageGrid.innerHTML = "";
    for (const img of images) {
        const card = document.createElement("div");
        card.className = "image-card";
        card.dataset.filename = img.filename;

        const thumbUrl = `/api/thumbnail/${encodeURIComponent(img.filename)}?folder=${encodeURIComponent(currentFolder)}`;

        const imgEl = document.createElement("img");
        imgEl.src = thumbUrl;
        imgEl.alt = img.filename;
        imgEl.loading = "lazy";
        card.appendChild(imgEl);

        const info = document.createElement("div");
        info.className = "card-info";

        const nameSpan = document.createElement("span");
        nameSpan.className = "filename";
        nameSpan.title = img.filename;
        nameSpan.textContent = img.filename;
        info.appendChild(nameSpan);

        const badge = document.createElement("span");
        badge.className = `badge ${img.tagged ? "badge-tagged" : "badge-untagged"}`;
        badge.textContent = img.tagged ? "Tagged" : "Untagged";
        info.appendChild(badge);

        card.appendChild(info);
        imageGrid.appendChild(card);
    }
}

async function tagAll() {
    const untagged = images.filter((img) => !img.tagged);
    if (untagged.length === 0) {
        progressText.textContent = "All images already tagged.";
        return;
    }

    tagAllBtn.disabled = true;
    loadBtn.disabled = true;
    progressBar.style.display = "inline-block";
    progressBar.max = untagged.length;
    progressBar.value = 0;

    let successCount = 0;

    for (let i = 0; i < untagged.length; i++) {
        const img = untagged[i];
        progressText.textContent = `Tagging ${i + 1} of ${untagged.length}: ${img.filename}`;
        progressBar.value = i;

        try {
            const resp = await fetch("/api/tag", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ folder: currentFolder, filename: img.filename }),
            });
            const result = await resp.json();

            const card = imageGrid.querySelector(`[data-filename="${CSS.escape(img.filename)}"]`);
            if (!card) continue;
            const badge = card.querySelector(".badge");

            if (result.status === "success") {
                badge.className = "badge badge-tagged";
                badge.textContent = "Tagged";
                img.tagged = true;
                successCount++;
            } else if (result.status === "skipped") {
                badge.className = "badge badge-skipped";
                badge.textContent = result.message;
            } else {
                badge.className = "badge badge-error";
                badge.textContent = "Error";
            }
        } catch (err) {
            const card = imageGrid.querySelector(`[data-filename="${CSS.escape(img.filename)}"]`);
            if (card) {
                const badge = card.querySelector(".badge");
                badge.className = "badge badge-error";
                badge.textContent = "Error";
            }
        }
    }

    progressBar.value = untagged.length;
    progressText.textContent = `Done. Tagged ${successCount} of ${untagged.length} images.`;
    tagAllBtn.disabled = false;
    loadBtn.disabled = false;
}
