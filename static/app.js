document.addEventListener("click", async (event) => {
  if (event.target.matches(".add-btn")) {
    startAddEntry(event.target);
  } else if (event.target.matches(".del-btn")) {
    await deleteEntry(event.target);
  }
});

function startAddEntry(addBtn) {
  const cell = addBtn.closest(".entries-cell");
  if (cell.querySelector(".entry-form")) return;

  addBtn.style.display = "none";

  const form = document.createElement("form");
  form.className = "entry-form";
  form.innerHTML = '<input type="text" maxlength="200" placeholder="z.B. 5km laufen" autocomplete="off">';
  cell.appendChild(form);

  const input = form.querySelector("input");
  input.focus();

  const cancel = () => {
    form.remove();
    addBtn.style.display = "";
  };

  input.addEventListener("keydown", (e) => {
    if (e.key === "Escape") cancel();
  });
  input.addEventListener("blur", () => {
    setTimeout(() => {
      if (document.activeElement !== input) cancel();
    }, 100);
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) {
      cancel();
      return;
    }
    const entriesContainer = cell.querySelector(".entries");
    const response = await fetch("/entries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        person: cell.dataset.person,
        date: cell.dataset.date,
        text: text,
      }),
    });
    if (response.ok) {
      const entry = await response.json();
      entriesContainer.appendChild(renderChip(entry));
    }
    cancel();
  });
}

function renderChip(entry) {
  const chip = document.createElement("span");
  chip.className = "chip";
  chip.dataset.id = entry.id;
  chip.textContent = entry.text;

  const delBtn = document.createElement("button");
  delBtn.className = "del-btn";
  delBtn.dataset.id = entry.id;
  delBtn.setAttribute("aria-label", "Löschen");
  delBtn.textContent = "×";
  chip.appendChild(delBtn);

  return chip;
}

async function deleteEntry(delBtn) {
  const id = delBtn.dataset.id;
  const response = await fetch(`/entries/${id}`, { method: "DELETE" });
  if (response.ok) {
    delBtn.closest(".chip").remove();
  }
}
