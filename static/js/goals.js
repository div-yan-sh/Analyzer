// Goals Management Scripts

document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("goalsGrid")) {
        loadGoals();

        // Listen for Goal Form modal submit
        const goalForm = document.getElementById("goalForm");
        goalForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const goalId = document.getElementById("goalId").value;
            const payload = {
                title: document.getElementById("goalTitle").value,
                target_amount: parseFloat(document.getElementById("goalTarget").value),
                current_amount: parseFloat(document.getElementById("goalCurrent").value || 0.0),
                deadline: document.getElementById("goalDeadline").value,
                description: document.getElementById("goalDescription").value
            };

            const url = goalId ? `/api/goals/${goalId}` : '/api/goals';
            const method = goalId ? 'PUT' : 'POST';

            try {
                const res = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (res.ok) {
                    closeGoalModal();
                    loadGoals();
                } else {
                    const data = await res.json();
                    alert("Error: " + (data.error || "Failed to save goal"));
                }
            } catch (err) {
                console.error("Goal save error", err);
            }
        });
    }
});

// Load and render goals grid list
async function loadGoals() {
    const grid = document.getElementById("goalsGrid");
    if (!grid) return;

    try {
        const res = await fetch('/api/goals');
        if (!res.ok) return;
        const data = await res.json();

        if (data.length === 0) {
            grid.innerHTML = `
                <div class="col-span-full py-12 text-center space-y-3">
                    <p class="text-slate-400 text-sm">No savings goals configured yet.</p>
                    <button onclick="openGoalModal()" class="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow">Add Your First Goal</button>
                </div>
            `;
            return;
        }

        grid.innerHTML = "";
        data.forEach(g => {
            const card = document.createElement("div");
            
            // Layout modifiers based on status
            const isCompleted = g.status === 'completed';
            const cardBg = isCompleted 
                ? "bg-slate-50 dark:bg-slate-800/20 border-slate-200 dark:border-slate-800 opacity-80" 
                : "bg-white dark:bg-darkCard border-lightBorder dark:border-darkBorder shadow-sm";

            const checkIcon = isCompleted 
                ? "fa-circle-check text-emerald-500" 
                : "fa-circle text-slate-300 dark:text-slate-700 hover:text-blue-500";

            const progressColor = isCompleted ? "bg-emerald-500" : "bg-blue-600";

            const deadlineObj = new Date(g.deadline);
            const deadlineStr = deadlineObj.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });

            card.className = `p-6 rounded-2xl border ${cardBg} space-y-4 flex flex-col justify-between transition-all`;
            card.innerHTML = `
                <div class="space-y-2">
                    <div class="flex justify-between items-start">
                        <button onclick="toggleGoalStatus(${g.id}, '${g.status}')" class="text-lg focus:outline-none transition-colors">
                            <i class="fa-solid ${checkIcon}"></i>
                        </button>
                        <div class="flex gap-2">
                            <button onclick="editGoal(${g.id})" class="text-xs text-slate-400 hover:text-blue-500"><i class="fa-solid fa-pen"></i></button>
                            <button onclick="deleteGoal(${g.id})" class="text-xs text-slate-400 hover:text-rose-500"><i class="fa-solid fa-trash"></i></button>
                        </div>
                    </div>

                    <div class="space-y-1">
                        <h4 class="font-semibold text-slate-900 dark:text-white leading-tight ${isCompleted ? 'line-through text-slate-400' : ''}">${g.title}</h4>
                        <p class="text-xs text-slate-400 truncate max-w-[200px]">${g.description || "No description"}</p>
                    </div>
                </div>

                <div class="space-y-2">
                    <div class="flex justify-between text-xs font-semibold">
                        <span class="text-slate-400">Progress</span>
                        <span class="text-slate-900 dark:text-white">${g.percentage}%</span>
                    </div>
                    <!-- Bar -->
                    <div class="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                        <div class="h-full rounded-full ${progressColor} transition-all duration-500" style="width: ${g.percentage}%"></div>
                    </div>
                    <div class="flex justify-between text-[10px] text-slate-400 font-bold uppercase">
                        <span>Saved: ₹${g.current_amount}</span>
                        <span>Target: ₹${g.target_amount}</span>
                    </div>
                </div>

                <div class="pt-3 border-t border-lightBorder dark:border-darkBorder space-y-1 text-xs">
                    <div class="flex justify-between text-slate-500">
                        <span>Deadline:</span>
                        <span class="font-medium text-slate-700 dark:text-slate-300">${deadlineStr}</span>
                    </div>
                    ${!isCompleted ? `
                    <div class="flex justify-between text-slate-500">
                        <span>Required Save:</span>
                        <span class="font-bold text-blue-600 dark:text-blue-400">₹${g.suggested_monthly_contribution.toFixed(0)} / mo</span>
                    </div>
                    ` : `
                    <div class="text-emerald-500 font-bold text-center pt-1 text-[10px] uppercase tracking-wider">Goal Accomplished!</div>
                    `}
                </div>
            `;
            grid.appendChild(card);
        });

    } catch (err) {
        console.error("Load goals error", err);
    }
}

// Modal actions
function openGoalModal(goal = null) {
    const modal = document.getElementById("goalModal");
    const modalTitle = document.getElementById("modalTitle");
    const form = document.getElementById("goalForm");

    modal.classList.remove("hidden");
    form.reset();

    if (goal) {
        modalTitle.innerText = "Edit Savings Goal";
        document.getElementById("goalId").value = goal.id;
        document.getElementById("goalTitle").value = goal.title;
        document.getElementById("goalTarget").value = goal.target_amount;
        document.getElementById("goalCurrent").value = goal.current_amount;
        document.getElementById("goalDeadline").value = goal.deadline;
        document.getElementById("goalDescription").value = goal.description;
    } else {
        modalTitle.innerText = "Set Savings Goal";
        document.getElementById("goalId").value = "";
        document.getElementById("goalDeadline").value = new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]; // Default 6 months in future
    }
}

function closeGoalModal() {
    document.getElementById("goalModal").classList.add("hidden");
}

// Fetch single record for editing
async function editGoal(id) {
    try {
        const res = await fetch('/api/goals');
        if (!res.ok) return;
        const data = await res.json();
        const goal = data.find(g => g.id === id);
        if (goal) {
            openGoalModal(goal);
        }
    } catch (err) {
        console.error("Goal fetch edit error", err);
    }
}

// Toggle status (Active <-> Completed)
async function toggleGoalStatus(id, currentStatus) {
    const newStatus = currentStatus === 'active' ? 'completed' : 'active';
    try {
        const res = await fetch(`/api/goals/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        if (res.ok) {
            loadGoals();
        }
    } catch (err) {
        console.error("Toggle goal error", err);
    }
}

// Delete Savings Goal
async function deleteGoal(id) {
    if (!confirm("Are you sure you want to delete this savings goal?")) return;
    try {
        const res = await fetch(`/api/goals/${id}`, { method: 'DELETE' });
        if (res.ok) {
            loadGoals();
        }
    } catch (err) {
        console.error("Delete goal error", err);
    }
}
