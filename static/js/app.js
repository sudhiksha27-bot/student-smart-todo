/**
 * Smart To-Do Assistant - Modern Student UI Application Logic
 * Integrates Flask REST APIs with MySQL Database backend.
 */

// Application State
const state = {
  tasks: [],
  categories: [],
  stats: null,
  activeDueFilter: '', // '', 'overdue', 'today', 'upcoming'
  searchQuery: '',
  activeCategory: '',
  activePriority: '',
  activeStatus: '',
  sortBy: 'priority_due',
  whatNextMode: 'balanced',
  autoPriorityTimer: null
};

// DOM Elements
const elements = {
  dbBadge: document.getElementById('dbBadge'),
  dbBadgeText: document.getElementById('dbBadgeText'),
  footerDbIndicator: document.getElementById('footerDbIndicator'),
  smartReminderBanner: document.getElementById('smartReminderBanner'),
  alertSummary: document.getElementById('alertSummary'),
  viewOverdueBtn: document.getElementById('viewOverdueBtn'),
  viewDueTodayBtn: document.getElementById('viewDueTodayBtn'),
  statTotal: document.getElementById('statTotal'),
  statActive: document.getElementById('statActive'),
  statCompletionRate: document.getElementById('statCompletionRate'),
  statProgressBar: document.getElementById('statProgressBar'),
  statCompletedText: document.getElementById('statCompletedText'),
  statOverdue: document.getElementById('statOverdue'),
  statDueToday: document.getElementById('statDueToday'),
  cardOverdue: document.getElementById('cardOverdue'),
  cardDueToday: document.getElementById('cardDueToday'),
  nlpForm: document.getElementById('nlpForm'),
  nlpInput: document.getElementById('nlpInput'),
  searchInput: document.getElementById('searchInput'),
  clearSearchBtn: document.getElementById('clearSearchBtn'),
  dueFilterGroup: document.getElementById('dueFilterGroup'),
  pillCountOverdue: document.getElementById('pillCountOverdue'),
  pillCountToday: document.getElementById('pillCountToday'),
  categoryFilter: document.getElementById('categoryFilter'),
  priorityFilter: document.getElementById('priorityFilter'),
  statusFilter: document.getElementById('statusFilter'),
  sortBy: document.getElementById('sortBy'),
  resetFiltersBtn: document.getElementById('resetFiltersBtn'),
  taskSectionTitle: document.getElementById('taskSectionTitle'),
  taskCountBadge: document.getElementById('taskCountBadge'),
  tasksGrid: document.getElementById('tasksGrid'),
  // Task Modal
  taskModal: document.getElementById('taskModal'),
  modalTitle: document.getElementById('modalTitle'),
  closeModalBtn: document.getElementById('closeModalBtn'),
  cancelModalBtn: document.getElementById('cancelModalBtn'),
  taskForm: document.getElementById('taskForm'),
  taskId: document.getElementById('taskId'),
  formTitle: document.getElementById('formTitle'),
  formCategory: document.getElementById('formCategory'),
  formPriority: document.getElementById('formPriority'),
  formDueDate: document.getElementById('formDueDate'),
  formEstimatedMinutes: document.getElementById('formEstimatedMinutes'),
  formStatus: document.getElementById('formStatus'),
  formDescription: document.getElementById('formDescription'),
  autoPrioritySuggestion: document.getElementById('autoPrioritySuggestion'),
  suggestedPriorityBadge: document.getElementById('suggestedPriorityBadge'),
  suggestedPriorityReason: document.getElementById('suggestedPriorityReason'),
  applyAutoPriorityBtn: document.getElementById('applyAutoPriorityBtn'),
  openNewTaskBtn: document.getElementById('openNewTaskBtn'),
  // What Next Modal
  whatNextBtn: document.getElementById('whatNextBtn'),
  whatNextModal: document.getElementById('whatNextModal'),
  closeWhatNextBtn: document.getElementById('closeWhatNextBtn'),
  whatNextContent: document.getElementById('whatNextContent'),
  // Daily Plan Modal
  dailyPlanBtn: document.getElementById('dailyPlanBtn'),
  dailyPlanModal: document.getElementById('dailyPlanModal'),
  closeDailyPlanBtn: document.getElementById('closeDailyPlanBtn'),
  dailyPlanContent: document.getElementById('dailyPlanContent'),
  toast: document.getElementById('toast')
};

// -----------------------------------------------------------------------------
// Toast Notification
// -----------------------------------------------------------------------------
function showToast(message, isError = false) {
  elements.toast.textContent = message;
  elements.toast.style.background = isError ? '#991b1b' : '#1e293b';
  elements.toast.classList.remove('hidden');
  setTimeout(() => {
    elements.toast.classList.add('hidden');
  }, 3500);
}

// -----------------------------------------------------------------------------
// Database Connection Diagnostics
// -----------------------------------------------------------------------------
async function fetchDbInfo() {
  try {
    const res = await fetch('/api/db-info');
    const data = await res.json();
    elements.dbBadge.className = `db-badge connected`;
    elements.dbBadgeText.textContent = `${data.label} (${data.database})`;
    elements.footerDbIndicator.textContent = `${data.label} &bull; ${data.host}`;
  } catch (err) {
    elements.dbBadge.className = 'db-badge';
    elements.dbBadgeText.textContent = 'DB Offline';
  }
}

// -----------------------------------------------------------------------------
// Categories
// -----------------------------------------------------------------------------
async function fetchCategories() {
  try {
    const res = await fetch('/api/categories');
    state.categories = await res.json();

    // Populate category filter dropdown
    elements.categoryFilter.innerHTML = '<option value="">All Categories</option>' + 
      state.categories.map(c => `<option value="${c.id}">${c.name} (${c.total_tasks || 0})</option>`).join('');

    // Populate modal select
    elements.formCategory.innerHTML = state.categories.map(c => 
      `<option value="${c.id}">${c.name}</option>`
    ).join('');
  } catch (err) {
    console.error('Error fetching categories:', err);
  }
}

// -----------------------------------------------------------------------------
// Stats & Productivity Dashboard
// -----------------------------------------------------------------------------
async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    state.stats = data;

    const ov = data.overview;
    elements.statTotal.textContent = ov.total;
    const activeCount = (ov.pending || 0) + (ov.in_progress || 0);
    elements.statActive.textContent = `${activeCount} active tasks`;

    elements.statCompletionRate.textContent = `${ov.completion_rate}%`;
    elements.statProgressBar.style.width = `${ov.completion_rate}%`;
    elements.statCompletedText.textContent = `${ov.completed} of ${ov.total} completed`;

    elements.statOverdue.textContent = ov.overdue;
    elements.statDueToday.textContent = ov.due_today;

    elements.pillCountOverdue.textContent = ov.overdue;
    elements.pillCountToday.textContent = ov.due_today;

    // Show or hide smart reminder banner
    if (ov.overdue > 0 || ov.due_today > 0) {
      elements.smartReminderBanner.classList.remove('hidden');
      const messages = [];
      if (ov.overdue > 0) messages.push(`${ov.overdue} overdue task${ov.overdue > 1 ? 's' : ''}`);
      if (ov.due_today > 0) messages.push(`${ov.due_today} due today`);
      elements.alertSummary.textContent = `Action required: You have ${messages.join(' and ')}.`;
    } else {
      elements.smartReminderBanner.classList.add('hidden');
    }
  } catch (err) {
    console.error('Error loading stats:', err);
  }
}

// -----------------------------------------------------------------------------
// Fetch and Render Tasks
// -----------------------------------------------------------------------------
async function fetchTasks() {
  elements.tasksGrid.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <p>Fetching tasks from MySQL database...</p>
    </div>
  `;

  const params = new URLSearchParams();
  if (state.activeCategory) params.append('category_id', state.activeCategory);
  if (state.activePriority) params.append('priority', state.activePriority);
  if (state.activeStatus) params.append('status', state.activeStatus);
  if (state.activeDueFilter) params.append('due_filter', state.activeDueFilter);
  if (state.searchQuery) params.append('search', state.searchQuery);
  if (state.sortBy) params.append('sort_by', state.sortBy);

  try {
    const res = await fetch(`/api/tasks?${params.toString()}`);
    state.tasks = await res.json();
    renderTasksList();
  } catch (err) {
    elements.tasksGrid.innerHTML = `
      <div class="empty-state">
        <p style="color: var(--danger)">Failed to load tasks. Please verify database connection.</p>
      </div>
    `;
  }
}

function formatDisplayDate(dateStr, isOverdue, isDueToday) {
  if (!dateStr) return 'No due date';
  try {
    const date = new Date(dateStr.replace(' ', 'T'));
    const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    if (isOverdue) {
      return `<span class="due-indicator overdue">⚠️ Overdue (${date.toLocaleDateString([], { month: 'short', day: 'numeric' })})</span>`;
    }
    if (isDueToday) {
      return `<span class="due-indicator today">⏰ Today at ${timeStr}</span>`;
    }
    return `<span class="due-indicator">📅 ${date.toLocaleDateString([], { month: 'short', day: 'numeric' })} at ${timeStr}</span>`;
  } catch (e) {
    return dateStr;
  }
}

function renderTasksList() {
  elements.taskCountBadge.textContent = `${state.tasks.length} task${state.tasks.length === 1 ? '' : 's'}`;

  if (state.activeDueFilter === 'overdue') {
    elements.taskSectionTitle.textContent = '⚠️ Overdue Tasks';
  } else if (state.activeDueFilter === 'today') {
    elements.taskSectionTitle.textContent = '⏰ Tasks Due Today';
  } else if (state.activeDueFilter === 'upcoming') {
    elements.taskSectionTitle.textContent = '📅 Upcoming Tasks';
  } else {
    elements.taskSectionTitle.textContent = 'All Tasks';
  }

  if (state.tasks.length === 0) {
    elements.tasksGrid.innerHTML = `
      <div class="empty-state">
        <p style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.35rem;">No tasks match your filter criteria.</p>
        <p style="color: var(--text-muted); font-size: 0.85rem;">Try adjusting the filter options or use the natural language bar to add one!</p>
      </div>
    `;
    return;
  }

  elements.tasksGrid.innerHTML = state.tasks.map(t => {
    const isCompleted = t.status === 'Completed';
    const cardClass = `task-card ${t.is_overdue ? 'is-overdue' : ''} ${t.is_due_today ? 'is-due-today' : ''} ${isCompleted ? 'is-completed' : ''}`;

    return `
      <div class="${cardClass}" data-id="${t.id}">
        <div class="task-top">
          <div class="status-checkbox ${isCompleted ? 'checked' : ''}" 
               title="Mark ${isCompleted ? 'Pending' : 'Completed'}"
               onclick="handleToggleStatus(${t.id}, '${isCompleted ? 'Pending' : 'Completed'}')">
            ${isCompleted ? '✓' : ''}
          </div>

          <div class="task-body">
            <div class="task-badges">
              <span class="category-badge">
                <span class="category-dot" style="background-color: ${t.category_color}"></span>
                ${t.category_name}
              </span>
              <span class="priority-badge priority-${t.priority}">
                ${t.priority} Priority
              </span>
              ${t.status === 'In Progress' ? '<span class="priority-badge" style="background: #e0f2fe; color: #0369a1;">⚡ In Progress</span>' : ''}
            </div>

            <h3 class="task-title">${escapeHtml(t.title)}</h3>
            ${t.description ? `<p class="task-desc">${escapeHtml(t.description)}</p>` : ''}
          </div>
        </div>

        <div class="task-bottom">
          <div class="task-meta-left">
            ${formatDisplayDate(t.due_date, t.is_overdue, t.is_due_today)}
            <span class="time-est" title="Estimated duration">⏱️ ${t.estimated_minutes}m</span>
          </div>

          <div class="task-actions">
            <button class="action-btn" title="Edit Task" onclick="handleEditTask(${t.id})">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            </button>
            <button class="action-btn delete" title="Delete Task" onclick="handleDeleteTask(${t.id})">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>'"]/g, 
    tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
  );
}

// -----------------------------------------------------------------------------
// Natural Language Task Creation
// -----------------------------------------------------------------------------
elements.nlpForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const prompt = elements.nlpInput.value.trim();
  if (!prompt) return;

  const submitBtn = document.getElementById('nlpSubmitBtn');
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span>Creating...</span>';

  try {
    const res = await fetch('/api/smart/nlp-add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt })
    });
    const data = await res.json();
    if (res.ok) {
      showToast(`✨ Created: "${data.task.title}" (${data.task.priority} Priority, Due: ${data.task.due_date.substring(0, 16)})`);
      elements.nlpInput.value = '';
      await fetchStats();
      await fetchTasks();
    } else {
      showToast(data.error || 'Failed to parse task', true);
    }
  } catch (err) {
    showToast('Network error while processing task', true);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<span>Create Task</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
  }
});

// Quick prompt suggestions
document.querySelectorAll('.chip-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    elements.nlpInput.value = btn.dataset.prompt;
    elements.nlpInput.focus();
  });
});

// -----------------------------------------------------------------------------
// Status Toggle (Complete / Pending)
// -----------------------------------------------------------------------------
async function handleToggleStatus(taskId, newStatus) {
  try {
    const res = await fetch(`/api/tasks/${taskId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    if (res.ok) {
      showToast(newStatus === 'Completed' ? '🎉 Task completed!' : 'Task marked as pending.');
      await fetchStats();
      await fetchTasks();
    } else {
      showToast('Could not update task status', true);
    }
  } catch (err) {
    showToast('Error updating status', true);
  }
}

// -----------------------------------------------------------------------------
// Delete Task
// -----------------------------------------------------------------------------
async function handleDeleteTask(taskId) {
  if (!confirm('Are you sure you want to delete this task?')) return;
  try {
    const res = await fetch(`/api/tasks/${taskId}`, { method: 'DELETE' });
    if (res.ok) {
      showToast('Task deleted successfully.');
      await fetchStats();
      await fetchTasks();
    } else {
      showToast('Error deleting task', true);
    }
  } catch (err) {
    showToast('Network error while deleting task', true);
  }
}

// -----------------------------------------------------------------------------
// Auto-Priority Suggestion in Modal
// -----------------------------------------------------------------------------
function triggerAutoPriorityCheck() {
  clearTimeout(state.autoPriorityTimer);
  state.autoPriorityTimer = setTimeout(async () => {
    const title = elements.formTitle.value.trim();
    const dueDate = elements.formDueDate.value;
    if (title.length < 3) {
      elements.autoPrioritySuggestion.classList.add('hidden');
      return;
    }

    try {
      const res = await fetch('/api/smart/auto-priority', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, due_date: dueDate })
      });
      const data = await res.json();
      elements.suggestedPriorityBadge.textContent = data.suggested_priority;
      elements.suggestedPriorityBadge.className = `badge priority-${data.suggested_priority}`;
      elements.suggestedPriorityReason.textContent = data.reason;
      elements.autoPrioritySuggestion.classList.remove('hidden');

      elements.applyAutoPriorityBtn.onclick = () => {
        elements.formPriority.value = data.suggested_priority;
        elements.autoPrioritySuggestion.classList.add('hidden');
        showToast(`Priority set to ${data.suggested_priority}`);
      };
    } catch (e) {
      console.warn('Auto priority error:', e);
    }
  }, 400);
}

elements.formTitle.addEventListener('input', triggerAutoPriorityCheck);
elements.formDueDate.addEventListener('change', triggerAutoPriorityCheck);

// Quick minutes buttons in modal
document.querySelectorAll('.min-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    elements.formEstimatedMinutes.value = chip.dataset.min;
  });
});

// -----------------------------------------------------------------------------
// Add / Edit Modal Controls
// -----------------------------------------------------------------------------
function openNewTaskModal() {
  elements.modalTitle.textContent = 'Create New Task';
  elements.taskId.value = '';
  elements.taskForm.reset();

  // Set default due date to tomorrow at 5:00 PM
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  tomorrow.setHours(17, 0, 0, 0);
  const tzOffset = tomorrow.getTimezoneOffset() * 60000;
  const localISOTime = new Date(tomorrow.getTime() - tzOffset).toISOString().slice(0, 16);
  elements.formDueDate.value = localISOTime;
  elements.formEstimatedMinutes.value = 45;
  elements.formPriority.value = 'Medium';
  elements.formStatus.value = 'Pending';
  elements.autoPrioritySuggestion.classList.add('hidden');

  elements.taskModal.classList.remove('hidden');
  elements.formTitle.focus();
}

async function handleEditTask(taskId) {
  const task = state.tasks.find(t => t.id === taskId);
  if (!task) return;

  elements.modalTitle.textContent = 'Edit Task';
  elements.taskId.value = task.id;
  elements.formTitle.value = task.title;
  elements.formCategory.value = task.category_id || (state.categories[0] ? state.categories[0].id : '');
  elements.formPriority.value = task.priority;
  elements.formEstimatedMinutes.value = task.estimated_minutes || 30;
  elements.formStatus.value = task.status;
  elements.formDescription.value = task.description || '';

  if (task.due_date) {
    const d = new Date(task.due_date.replace(' ', 'T'));
    const tzOffset = d.getTimezoneOffset() * 60000;
    elements.formDueDate.value = new Date(d.getTime() - tzOffset).toISOString().slice(0, 16);
  }

  elements.autoPrioritySuggestion.classList.add('hidden');
  elements.taskModal.classList.remove('hidden');
}

elements.openNewTaskBtn.addEventListener('click', openNewTaskModal);
elements.closeModalBtn.addEventListener('click', () => elements.taskModal.classList.add('hidden'));
elements.cancelModalBtn.addEventListener('click', () => elements.taskModal.classList.add('hidden'));

// Save Task Form Submission
elements.taskForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const id = elements.taskId.value;
  const taskData = {
    title: elements.formTitle.value.trim(),
    category_id: parseInt(elements.formCategory.value),
    priority: elements.formPriority.value,
    due_date: elements.formDueDate.value,
    estimated_minutes: parseInt(elements.formEstimatedMinutes.value),
    status: elements.formStatus.value,
    description: elements.formDescription.value.trim()
  };

  const isEdit = Boolean(id);
  const url = isEdit ? `/api/tasks/${id}` : '/api/tasks';
  const method = isEdit ? 'PUT' : 'POST';

  try {
    const res = await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(taskData)
    });
    if (res.ok) {
      showToast(isEdit ? 'Task updated successfully' : 'Task added successfully');
      elements.taskModal.classList.add('hidden');
      await fetchStats();
      await fetchTasks();
    } else {
      const err = await res.json();
      showToast(err.error || 'Failed to save task', true);
    }
  } catch (err) {
    showToast('Network error saving task', true);
  }
});

// -----------------------------------------------------------------------------
// "What Should I Do Next?" Assistant
// -----------------------------------------------------------------------------
async function openWhatNextAssistant(mode = 'balanced') {
  state.whatNextMode = mode;
  elements.whatNextModal.classList.remove('hidden');
  elements.whatNextContent.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <p>Analyzing pending assignments, deadlines & workloads...</p>
    </div>
  `;

  // Update mode chips
  document.querySelectorAll('.mode-chip').forEach(c => {
    c.classList.toggle('active', c.dataset.mode === mode);
  });

  try {
    const res = await fetch(`/api/smart/what-next?mode=${mode}`);
    const data = await res.json();

    if (!data.has_tasks) {
      elements.whatNextContent.innerHTML = `
        <div class="empty-state">
          <p style="font-size: 1.2rem; font-weight: 700;">${data.message}</p>
        </div>
      `;
      return;
    }

    const t = data.best_task;
    elements.whatNextContent.innerHTML = `
      <div class="recommendation-card">
        <div class="recommendation-score-pill">
          Priority Score: ${data.score} pts
        </div>
        
        <div>
          <span class="category-badge">
            <span class="category-dot" style="background-color: ${t.category_color}"></span>
            ${t.category_name}
          </span>
          <span class="priority-badge priority-${t.priority}" style="margin-left: 0.35rem;">
            ${t.priority} Priority
          </span>
        </div>

        <h2 style="font-size: 1.3rem; font-weight: 800; color: var(--text-main); line-height: 1.3;">
          ${escapeHtml(t.title)}
        </h2>

        ${t.description ? `<p style="font-size: 0.88rem; color: var(--text-muted);">${escapeHtml(t.description)}</p>` : ''}

        <div style="display: flex; gap: 1rem; font-size: 0.85rem; font-weight: 600; color: var(--text-muted); margin-top: 0.25rem;">
          <span>⏱️ Estimated: ${t.estimated_minutes} mins</span>
          <span>📅 Due: ${t.due_date}</span>
        </div>

        <div class="recommendation-reason-box">
          <strong>Why this task now?</strong><br>
          ${data.recommendation_reason}
        </div>

        <div style="display: flex; gap: 0.75rem; margin-top: 0.5rem;">
          <button class="btn btn-primary" onclick="startTaskNow(${t.id})">
            ⚡ Start Working on This
          </button>
          <button class="btn btn-secondary" onclick="handleToggleStatus(${t.id}, 'Completed'); elements.whatNextModal.classList.add('hidden');">
            Mark Done
          </button>
        </div>
      </div>

      ${data.runner_up ? `
        <div class="runner-up-card">
          <h5>Runner Up Alternative</h5>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
              <strong>${escapeHtml(data.runner_up.title)}</strong>
              <div style="font-size: 0.78rem; color: var(--text-muted);">
                ${data.runner_up.priority} Priority &bull; ${data.runner_up.estimated_minutes}m &bull; ${data.runner_up.category_name}
              </div>
            </div>
            <button class="btn btn-xs btn-outline" onclick="startTaskNow(${data.runner_up.id})">Switch to This</button>
          </div>
        </div>
      ` : ''}
    `;
  } catch (e) {
    elements.whatNextContent.innerHTML = `<p style="color: var(--danger)">Error calculating recommendation.</p>`;
  }
}

async function startTaskNow(taskId) {
  await handleToggleStatus(taskId, 'In Progress');
  elements.whatNextModal.classList.add('hidden');
  showToast('Task marked In Progress! Let\'s focus on it.');
}

elements.whatNextBtn.addEventListener('click', () => openWhatNextAssistant('balanced'));
elements.closeWhatNextBtn.addEventListener('click', () => elements.whatNextModal.classList.add('hidden'));

document.querySelectorAll('.mode-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    openWhatNextAssistant(chip.dataset.mode);
  });
});

// -----------------------------------------------------------------------------
// Daily Plan Generator
// -----------------------------------------------------------------------------
async function openDailyPlan() {
  elements.dailyPlanModal.classList.remove('hidden');
  elements.dailyPlanContent.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <p>Building your optimal daily study schedule...</p>
    </div>
  `;

  try {
    const res = await fetch('/api/smart/daily-plan');
    const data = await res.json();

    if (!data.schedule || data.schedule.length === 0) {
      elements.dailyPlanContent.innerHTML = `
        <div class="empty-state">
          <p style="font-weight: 700;">No pending tasks to schedule today!</p>
        </div>
      `;
      return;
    }

    elements.dailyPlanContent.innerHTML = `
      <div class="daily-plan-header">
        <div>
          <strong style="color: #312e81; font-size: 0.95rem;">Today's Planned Focus: ${data.task_count} Tasks</strong>
          <div style="font-size: 0.78rem; color: #4338ca;">Includes automatic mental reset & recharge breaks</div>
        </div>
        <div class="plan-stat">⏱️ ${data.total_duration} Study Time</div>
      </div>

      <div class="timeline">
        ${data.schedule.map(item => {
          if (item.type === 'break') {
            return `
              <div class="timeline-item break">
                <div class="timeline-time">${item.start_time} - ${item.end_time} (${item.duration_minutes}m)</div>
                <div class="timeline-title">${item.title}</div>
              </div>
            `;
          }

          const t = item.task;
          return `
            <div class="timeline-item">
              <div class="timeline-time">${item.start_time} - ${item.end_time} (${item.duration_minutes}m)</div>
              <div class="timeline-title">${escapeHtml(t.title)}</div>
              <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 0.2rem;">
                <span class="category-dot" style="background-color: ${t.category_color}; display: inline-block; vertical-align: middle; margin-right: 4px;"></span>
                ${t.category_name} &bull; <span class="priority-${t.priority}">${t.priority} Priority</span>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  } catch (err) {
    elements.dailyPlanContent.innerHTML = `<p style="color: var(--danger)">Could not generate daily schedule.</p>`;
  }
}

elements.dailyPlanBtn.addEventListener('click', openDailyPlan);
elements.closeDailyPlanBtn.addEventListener('click', () => elements.dailyPlanModal.classList.add('hidden'));

// -----------------------------------------------------------------------------
// Filters & Search Handling
// -----------------------------------------------------------------------------
elements.searchInput.addEventListener('input', (e) => {
  state.searchQuery = e.target.value.trim();
  elements.clearSearchBtn.classList.toggle('hidden', !state.searchQuery);
  fetchTasks();
});

elements.clearSearchBtn.addEventListener('click', () => {
  elements.searchInput.value = '';
  state.searchQuery = '';
  elements.clearSearchBtn.classList.add('hidden');
  fetchTasks();
});

elements.categoryFilter.addEventListener('change', (e) => {
  state.activeCategory = e.target.value;
  fetchTasks();
});

elements.priorityFilter.addEventListener('change', (e) => {
  state.activePriority = e.target.value;
  fetchTasks();
});

elements.statusFilter.addEventListener('change', (e) => {
  state.activeStatus = e.target.value;
  fetchTasks();
});

elements.sortBy.addEventListener('change', (e) => {
  state.sortBy = e.target.value;
  fetchTasks();
});

// Quick Due Filter Pills
document.querySelectorAll('#dueFilterGroup .pill').forEach(pill => {
  pill.addEventListener('click', () => {
    document.querySelectorAll('#dueFilterGroup .pill').forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    state.activeDueFilter = pill.dataset.due;
    fetchTasks();
  });
});

// Alert banner buttons
elements.viewOverdueBtn.addEventListener('click', () => {
  setDueFilter('overdue');
});
elements.viewDueTodayBtn.addEventListener('click', () => {
  setDueFilter('today');
});
elements.cardOverdue.addEventListener('click', () => {
  setDueFilter('overdue');
});
elements.cardDueToday.addEventListener('click', () => {
  setDueFilter('today');
});

function setDueFilter(dueType) {
  document.querySelectorAll('#dueFilterGroup .pill').forEach(p => {
    p.classList.toggle('active', p.dataset.due === dueType);
  });
  state.activeDueFilter = dueType;
  fetchTasks();
  elements.tasksGrid.scrollIntoView({ behavior: 'smooth' });
}

// Reset filters
elements.resetFiltersBtn.addEventListener('click', () => {
  state.activeCategory = '';
  state.activePriority = '';
  state.activeStatus = '';
  state.activeDueFilter = '';
  state.searchQuery = '';
  state.sortBy = 'priority_due';

  elements.searchInput.value = '';
  elements.categoryFilter.value = '';
  elements.priorityFilter.value = '';
  elements.statusFilter.value = '';
  elements.sortBy.value = 'priority_due';
  elements.clearSearchBtn.classList.add('hidden');

  document.querySelectorAll('#dueFilterGroup .pill').forEach(p => {
    p.classList.toggle('active', p.dataset.due === '');
  });

  fetchTasks();
});

// -----------------------------------------------------------------------------
// App Initialization
// -----------------------------------------------------------------------------
async function initApp() {
  await fetchDbInfo();
  await fetchCategories();
  await fetchStats();
  await fetchTasks();
}

window.addEventListener('DOMContentLoaded', initApp);

