/* ======================================================
   CSRF
====================================================== */
function getCSRF() {
  return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

/* ======================================================
   DATE HELPERS
====================================================== */
function today() {
  return new Date().toISOString().split("T")[0];
}

function addDays(dateStr, days) {
  const d = new Date(dateStr);
  d.setDate(d.getDate() + days);
  return d.toISOString().split("T")[0];
}

function formatDate(dateStr) {
  if (!dateStr) return "";
  return new Date(dateStr)
    .toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric"
    })
    .replace(/ /g, "-");
}

function hideConflictWarning(form) {
  const box = form.querySelector(".conflict-warning");
  if (box) box.style.display = "none";
}

/* ======================================================
   ELEMENTS
====================================================== */
const addModal = document.getElementById("addModal");
const editModal = document.getElementById("editModal");
const addForm = document.getElementById("addForm");
const editForm = document.getElementById("editForm");
const deleteBtn = document.getElementById("deleteBtn");

/* ======================================================
   OPEN ADD MODAL
====================================================== */
document.getElementById("newLeadBtn").onclick = () => {
  addForm.reset();
  addModal.style.display = "flex";
};

/* ======================================================
   CONFLICT CHECK
====================================================== */
async function checkLeadConflict(form) {
  const start = form.querySelector('[name="event_start_date"]').value;
  let session =
    form.querySelector('[name="event_start_session"]')?.value || "MOR";

  const sessionMap = { Morning: "MOR", Evening: "EVE", MOR: "MOR", EVE: "EVE" };
  session = sessionMap[session] || "MOR";

  if (!start) return false;

  const res = await fetch(
    `/leads/check-conflict/?date=${encodeURIComponent(start)}&session=${encodeURIComponent(session)}`,
    { credentials: "same-origin" }
  );

  if (!res.ok) return false;

  const data = await res.json();
  return data.success && data.conflicts.length ? data.conflicts : false;
}

function showConflictWarning(form, conflicts, onProceed = null) {
  const box = form.querySelector(".conflict-warning");
  if (!box) return;

  box.innerHTML = `
    <div class="warning-box">
      ⚠ <strong>Conflict with:</strong>
      ${conflicts.map(c => c.name).join(", ")}
      <br><br>
      ${onProceed ? `
        <button type="button" class="btn-warning proceed-btn">
          Proceed anyway
        </button>` : ""}
    </div>
  `;

  box.style.display = "block";

  if (onProceed) {
    box.querySelector(".proceed-btn").onclick = () => {
      box.style.display = "none";
      onProceed();
    };
  }
}

/* ======================================================
   CREATE LEAD CARD
====================================================== */
function createLeadCard(lead) {
  const card = document.createElement("div");
  card.className = "lead-card";
  card.dataset.id = lead.id;
  card.dataset.status = lead.status;

  card.dataset.name = (lead.name || "").toLowerCase();
  card.dataset.phone = (lead.phone || "").toLowerCase();
  card.dataset.email = (lead.email || "").toLowerCase();
  card.dataset.place = (lead.event_place || "").toLowerCase();
  card.dataset.eventType = (lead.event_type || "").toLowerCase();
  card.dataset.amount = lead.amount || 0;
  card.dataset.date = lead.event_start_date || "";

  const showFollowup =
    lead.followup_date &&
    (lead.status === "NEW" || lead.status === "FOLLOW");

  card.innerHTML = `
    <div class="card-inner">

      <div class="card-front">
        <div class="lead-header">
          <span class="lead-name">${lead.name}</span>
          <div class="lead-icons">
            <span class="icon edit-icon">✎</span>
            <span class="icon contact-icon">➤</span>
          </div>
        </div>

        <hr>

        <div class="row">
          <img src="/static/images/icon1.svg">
          <span>${lead.event_type || ""}</span>
        </div>

        <div class="row">
          <img src="/static/images/icon2.svg">
          <span>
            ${formatDate(lead.event_start_date)}
            ${lead.event_start_session === "MOR" ? "Mor" : "Eve"}
            →
            ${formatDate(lead.event_end_date)}
            ${lead.event_end_session === "MOR" ? "Mor" : "Eve"}
          </span>
        </div>

        ${showFollowup ? `
        <div class="row followup">
          <img src="/static/images/icon3.svg">
          <span class="follow-date">${formatDate(lead.followup_date)}</span>
          <span class="due-badge">DUE</span>
        </div>` : ""}

        <div class="row amount">
          <img src="/static/images/icon4.svg">
          <span>₹ ${Number(lead.amount).toLocaleString("en-IN")}</span>
        </div>
      </div>

      <div class="card-back">
        <div class="lead-header">
          <span class="lead-name">${lead.name}</span>
          <div class="lead-icons">
            <span class="icon edit-icon">✎</span>
            <span class="icon contact-icon">➤</span>
          </div>
        </div>
        <hr>
        ${lead.phone ? `<div>📞 ${lead.phone}</div>` : ""}
        ${lead.email ? `<div>📨 ${lead.email}</div>` : ""}
        ${lead.event_place ? `<div>📍 ${lead.event_place}</div>` : ""}
        ${lead.advance_amount ? `<div>$ Advance: ₹ ${lead.advance_amount}</div>` : ""}
        ${lead.remaining_amount ? `<div>$ To be paid: ₹ ${lead.amount - lead.advance_amount}</div>` : ""}
      </div>

    </div>
  `;

  // Flip
  const contactBtn = card.querySelector(".contact-icon");
  const cardBack = card.querySelector(".card-back");

  if (contactBtn) {
    contactBtn.onclick = e => {
      e.stopPropagation();
      card.classList.toggle("flipped");
    };
  }

  if (cardBack) {
    cardBack.onclick = e => {
      e.stopPropagation();
      card.classList.remove("flipped");
    };
  }

  // Edit
  card.querySelector(".edit-icon").onclick = e => {
    e.stopPropagation();
    openEdit(card);
  };

  return card;
}

/* ======================================================
   LOAD LEADS
====================================================== */
function renderBoard(data) {
  ["NEW", "FOLLOW", "ACCEPTED", "LOST"].forEach(status => {
    const col = document.getElementById(`cards-${status}`);
    col.innerHTML = "";

    data[status].forEach(lead => {
      autoMoveToLost(lead);
      col.appendChild(createLeadCard(lead));
    });

    document.getElementById(`count-${status.toLowerCase()}`).innerText =
      data[status].length;
  });
}

function loadLeads(query = "") {
  fetch(`/leads/list/?q=${encodeURIComponent(query)}`)
    .then(res => res.json())
    .then(data => {
      renderBoard(data);
      initSortable();
      updateAmounts();
      applyFilters();
    });
}


/* ======================================================
   AUTO MOVE TO LOST
====================================================== */
function autoMoveToLost(lead) {
  if (!lead.event_end_date) return;
  if (lead.status !== "NEW" && lead.status !== "FOLLOW") return;

  const endDate = new Date(lead.event_end_date);
  const todayDate = new Date();
  endDate.setHours(0, 0, 0, 0);
  todayDate.setHours(0, 0, 0, 0);

  if (endDate >= todayDate) return;

  fetch(`/leads/update-status/${lead.id}/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCSRF()
    },
    credentials: "same-origin",
    body: JSON.stringify({ status: "LOST" })
  });
}

/* ======================================================
   ADD LEAD
====================================================== */
addForm.addEventListener("submit", async e => {
  e.preventDefault();
  hideConflictWarning(addForm);

  if (!addForm.event_end_date.value && addForm.event_start_date.value) {
    addForm.event_end_date.value = addDays(addForm.event_start_date.value, 1);
  }

  const conflicts = await checkLeadConflict(addForm);
  if (conflicts) {
    showConflictWarning(addForm, conflicts);
    return;
  }

  fetch("/leads/add/", {
    method: "POST",
    body: new FormData(addForm),
    headers: { "X-CSRFToken": getCSRF() }
  }).then(() => {
    addModal.style.display = "none";
    loadLeads();
  });
});

/* ======================================================
   EDIT LEAD
====================================================== */
editForm.addEventListener("submit", async e => {
  e.preventDefault();
  hideConflictWarning(editForm);

  const conflicts = await checkLeadConflict(editForm);
  if (conflicts) {
    showConflictWarning(editForm, conflicts);
    return;
  }

  fetch("/leads/edit/", {
    method: "POST",
    body: new FormData(editForm),
    headers: { "X-CSRFToken": getCSRF() }
  }).then(() => {
    editModal.style.display = "none";
    loadLeads();
  });
});

/* ======================================================
   DELETE
====================================================== */
deleteBtn.onclick = () => {
  if (!confirm("Delete this lead?")) return;

  fetch("/leads/delete/", {
    method: "POST",
    headers: { "X-CSRFToken": getCSRF() },
    body: new URLSearchParams({ id: editForm.id.value })
  }).then(() => {
    editModal.style.display = "none";
    loadLeads();
  });
};

/* ======================================================
   SORTABLE
====================================================== */
function initSortable() {
  document.querySelectorAll(".cards").forEach(col => {
    new Sortable(col, {
      group: "leads",
      animation: 180,
      onAdd: evt => {
        const card = evt.item;
        const leadId = card.dataset.id;
        const newStatus = evt.to.closest(".column").dataset.status;
        const oldCol = evt.from;

        fetch(`/leads/update-status/${leadId}/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRF()
          },
          credentials: "same-origin",
          body: JSON.stringify({ status: newStatus })
        })
        .then(async res => {
          if (res.status === 409) {
            const data = await res.json();
            oldCol.appendChild(card);
            openEdit(card);
            setTimeout(() => {
              showConflictWarning(editForm, data.conflicts, () => {
                forceAccept(leadId);
                editModal.style.display = "none";
              });
            }, 50);
            throw new Error("Conflict");
          }

          if (!res.ok) throw new Error("Status update failed");
        })
        .catch(err => console.warn(err.message));
      }
    });
  });
}

function forceAccept(leadId) {
  fetch(`/leads/update-status/${leadId}/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCSRF()
    },
    credentials: "same-origin",
    body: JSON.stringify({ status: "ACCEPTED", override: true })
  }).then(() => loadLeads());
}

/* ======================================================
   OPEN EDIT MODAL
====================================================== */
function openEdit(card) {
  hideConflictWarning(editForm);
  editForm.id.value = card.dataset.id || "";

  [
    "name",
    "event_type",
    "amount",
    "event_start_date",
    "event_start_session",
    "event_end_date",
    "event_end_session",
    "phone",
    "email",
    "event_place",
    "followup_date",
    "advance_amount"
  ].forEach(field => {
    if (editForm[field]) editForm[field].value = card.dataset[field] || "";
  });

  editModal.style.display = "flex";
}

/* ======================================================
   INIT
====================================================== */
document.addEventListener("DOMContentLoaded", function () {

  loadLeads();
  initModals();
  /* ---------------- GLOBAL SEARCH ---------------- */
  const searchInput = document.getElementById("globalSearch");

    if (searchInput) {
      let searchTimer;

      searchInput.addEventListener("input", function () {
        clearTimeout(searchTimer);

        const query = this.value.trim();

        searchTimer = setTimeout(() => {
          loadLeads(query);
        }, 300);

      });
  }

  // FILTER INIT
  const filterBtn = document.getElementById("filterBtn");
  const dropdown = document.getElementById("filterDropdown");
  const statusCheckboxes = document.querySelectorAll("#filterDropdown input[type='checkbox']");
  const minAmountInput = document.getElementById("minAmount");
  const maxAmountInput = document.getElementById("maxAmount");
  const startDateInput = document.getElementById("startDate");
  const endDateInput = document.getElementById("endDate");
  const clearBtn = document.getElementById("clearFilters");

  filterBtn?.addEventListener("click", e => {
    e.stopPropagation();
    dropdown?.classList.toggle("show");
  });

  document.addEventListener("click", e => {
    if (dropdown && !dropdown.contains(e.target) && !e.target.closest("#filterBtn")) {
      dropdown.classList.remove("show");
    }
  });

  statusCheckboxes.forEach(cb => cb.addEventListener("change", applyFilters));
  minAmountInput?.addEventListener("input", applyFilters);
  maxAmountInput?.addEventListener("input", applyFilters);
  startDateInput?.addEventListener("change", applyFilters);
  endDateInput?.addEventListener("change", applyFilters);

  clearBtn?.addEventListener("click", () => {
    statusCheckboxes.forEach(cb => cb.checked = true);
    if (minAmountInput) minAmountInput.value = "";
    if (maxAmountInput) maxAmountInput.value = "";
    if (startDateInput) startDateInput.value = "";
    if (endDateInput) endDateInput.value = "";
    applyFilters();
  });

});

/* ======================================================
   MODAL OPEN/CLOSE FIX
====================================================== */

// Open Add Modal
document.getElementById("newLeadBtn")?.addEventListener("click", () => {
  addForm.reset();
  addModal.style.display = "flex";
});

// Close buttons using delegation
document.addEventListener("click", e => {
  // Add modal close
  if (e.target.closest("#addModal .close-btn") || e.target === addModal) {
    addModal.style.display = "none";
  }
  // Edit modal close
  if (e.target.closest("#editModal .close-btn") || e.target === editModal) {
    editModal.style.display = "none";
  }
});

/* ======================================================
   MODAL OPEN / CLOSE
====================================================== */
function initModals() {
  const modals = [addModal, editModal];

  modals.forEach(modal => {
    // Close when clicking outside modal-content
    modal.addEventListener("click", e => {
      if (e.target === modal) modal.style.display = "none";
    });

    // Close buttons
    modal.querySelectorAll(".modal-close").forEach(btn => {
      btn.addEventListener("click", () => modal.style.display = "none");
    });
  });
}

// Open Add Modal
document.getElementById("newLeadBtn")?.addEventListener("click", () => {
  addForm.reset();
  addModal.style.display = "flex";
});
