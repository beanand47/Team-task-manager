(function () {
  const publicPaths = new Set(["/login", "/signup"]);

  window.showToast = function showToast(message, type = "success") {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    window.setTimeout(() => toast.remove(), 3000);
  };

  window.getStoredUser = function getStoredUser() {
    try {
      return JSON.parse(localStorage.getItem("user") || "null");
    } catch (_error) {
      return null;
    }
  };

  window.initials = function initials(nameOrEmail) {
    const source = (nameOrEmail || "?").trim();
    const parts = source.split(/\s+/);
    if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    return source.slice(0, 2).toUpperCase();
  };

  window.formatDate = function formatDate(dateStr) {
    if (!dateStr) return "No date";
    return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(new Date(`${dateStr}T00:00:00`));
  };

  window.formatDateTime = function formatDateTime(dateStr) {
    if (!dateStr) return "Unknown";
    return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" }).format(new Date(dateStr));
  };

  window.isOverdue = function isOverdue(dateStr, status) {
    if (!dateStr || status === "done") return false;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const due = new Date(`${dateStr}T00:00:00`);
    return due < today;
  };

  window.statusBadge = function statusBadge(status) {
    const label = { todo: "Todo", in_progress: "In Progress", done: "Done" }[status] || status;
    return `<span class="badge status-${status}">${label}</span>`;
  };

  window.priorityBadge = function priorityBadge(priority) {
    const label = priority ? priority[0].toUpperCase() + priority.slice(1) : "Medium";
    return `<span class="badge priority-${priority || "medium"}">${label}</span>`;
  };

  document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("access_token");
    if (!publicPaths.has(window.location.pathname) && !token) {
      window.location.href = "/login";
      return;
    }

    const sidebar = document.querySelector(".sidebar");
    document.getElementById("sidebar-toggle")?.addEventListener("click", () => sidebar?.classList.toggle("open"));

    document.getElementById("logout-btn")?.addEventListener("click", () => {
      localStorage.clear();
      window.location.href = "/login";
    });

    const user = window.getStoredUser();
    if (user) {
      document.querySelectorAll("[data-user-name]").forEach((el) => { el.textContent = user.name; });
      document.querySelectorAll("[data-user-email]").forEach((el) => { el.textContent = user.email; });
      document.querySelectorAll("[data-user-initials]").forEach((el) => { el.textContent = window.initials(user.name || user.email); });
    }

    document.querySelectorAll(".nav-link").forEach((link) => {
      if (link.getAttribute("href") === window.location.pathname) link.classList.add("active");
    });

    const projectId = document.body.dataset.projectId;
    const membersLink = document.getElementById("project-members-link");
    if (projectId && membersLink) {
      membersLink.href = `/projects/${projectId}/members`;
      membersLink.style.display = "block";
      if (window.location.pathname === membersLink.getAttribute("href")) {
        membersLink.classList.add("active");
      }
    }
  });
})();
