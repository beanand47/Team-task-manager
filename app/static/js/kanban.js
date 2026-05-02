(function () {
  const statuses = ["todo", "in_progress", "done"];
  let board;
  let projectId;
  let tasks = [];

  function cardHtml(task) {
    const assignee = task.assignee_name || "Unassigned";
    const overdueClass = window.isOverdue(task.due_date, task.status) ? " overdue-card" : "";
    return `
      <article class="task-card${overdueClass}" draggable="true" data-task-id="${task.id}">
        <div class="task-title">${task.title}</div>
        <div class="task-meta">
          <span class="initials">${window.initials(assignee)}</span>
          ${window.priorityBadge(task.priority)}
          <span>${window.formatDate(task.due_date)}</span>
        </div>
      </article>
    `;
  }

  function renderTasks() {
    statuses.forEach((status) => {
      const column = board.querySelector(`[data-status="${status}"] .column-body`);
      column.innerHTML = tasks.filter((task) => task.status === status).map(cardHtml).join("");
    });
    bindCards();
    updateCounts();
  }

  function updateCounts() {
    statuses.forEach((status) => {
      const count = tasks.filter((task) => task.status === status).length;
      const badge = board.querySelector(`[data-status="${status}"] .count-badge`);
      if (badge) badge.textContent = count;
    });
  }

  function bindCards() {
    board.querySelectorAll(".task-card").forEach((card) => {
      card.addEventListener("dragstart", (event) => {
        event.dataTransfer.setData("text/plain", card.dataset.taskId);
      });
      card.addEventListener("click", () => {
        window.location.href = `/tasks/${card.dataset.taskId}`;
      });
    });
  }

  async function moveTask(taskId, newStatus) {
    const task = tasks.find((item) => item.id === taskId);
    if (!task || task.status === newStatus) return;
    const oldStatus = task.status;
    task.status = newStatus;
    renderTasks();
    try {
      const updated = await window.apiPut(`/api/tasks/${taskId}`, { status: newStatus });
      Object.assign(task, updated);
      renderTasks();
      window.showToast("Task moved");
    } catch (error) {
      task.status = oldStatus;
      renderTasks();
      window.showToast(error.message, "error");
    }
  }

  function bindColumns() {
    board.querySelectorAll(".kanban-column").forEach((column) => {
      column.addEventListener("dragover", (event) => event.preventDefault());
      column.addEventListener("drop", (event) => {
        event.preventDefault();
        moveTask(event.dataTransfer.getData("text/plain"), column.dataset.status);
      });
    });
  }

  async function loadTasks() {
    try {
      tasks = await window.apiGet(`/api/projects/${projectId}/tasks`);
      renderTasks();
    } catch (error) {
      window.showToast(error.message, "error");
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    board = document.querySelector("[data-kanban-board]");
    if (!board) return;
    projectId = board.dataset.projectId;
    bindColumns();
    loadTasks();
    window.reloadKanban = loadTasks;
  });
})();
