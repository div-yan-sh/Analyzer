// Budgets Management Scripts

document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("budgetsList")) {
        // Preselect current month/year in selector forms
        const now = new Date();
        document.getElementById("budgetMonth").value = (now.getMonth() + 1).toString();
        document.getElementById("budgetYear").value = now.getFullYear().toString();

        loadBudgets();
        loadTodaySpent();

        // Listen for budget configuration form
        const budgetForm = document.getElementById("budgetForm");
        budgetForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const payload = {
                amount: parseFloat(document.getElementById("budgetAmount").value),
                category: document.getElementById("budgetCategory").value,
                month: parseInt(document.getElementById("budgetMonth").value),
                year: parseInt(document.getElementById("budgetYear").value)
            };

            try {
                const res = await fetch('/api/budget', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                
                if (res.ok) {
                    loadBudgets();
                    document.getElementById("budgetAmount").value = "";
                } else {
                    alert("Error: " + (data.error || "Failed to set budget"));
                }
            } catch (err) {
                console.error("Budget save error", err);
            }
        });
    }
});

// Load and render budgets list
async function loadBudgets() {
    const list = document.getElementById("budgetsList");
    if (!list) return;

    const month = document.getElementById("budgetMonth").value;
    const year = document.getElementById("budgetYear").value;

    try {
        const res = await fetch(`/api/budget?month=${month}&year=${year}`);
        if (!res.ok) return;
        const data = await res.json();

        list.innerHTML = "";

        // Calculate and show recommended daily limit from overall budget
        const overall = data.utilization.find(u => u.category === "Overall");
        updateDailyGuideline(overall);

        data.utilization.forEach(u => {
            const card = document.createElement("div");
            card.className = "space-y-2";

            // Determine status color classes
            let progressColor = "bg-blue-600";
            let textColor = "text-blue-600 dark:text-blue-400";
            if (u.status_level === "success") {
                progressColor = "bg-emerald-500";
                textColor = "text-emerald-500";
            } else if (u.status_level === "warning") {
                progressColor = "bg-amber-500";
                textColor = "text-amber-500";
            } else if (u.status_level === "danger") {
                progressColor = "bg-rose-500";
                textColor = "text-rose-500";
            }

            card.innerHTML = `
                <div class="flex justify-between items-baseline">
                    <div>
                        <span class="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-wider">${u.category}</span>
                        <p class="text-[10px] text-slate-400 font-semibold">${u.warning_text}</p>
                    </div>
                    <div class="text-right">
                        <span class="text-xs font-bold text-slate-900 dark:text-white">₹${u.spent.toFixed(0)}</span>
                        <span class="text-xs text-slate-400">/ ₹${u.budget.toFixed(0)}</span>
                        <span class="text-xs font-semibold ml-2 ${textColor}">${u.percentage.toFixed(0)}%</span>
                    </div>
                </div>
                <!-- Utilization Bar -->
                <div class="w-full bg-slate-100 dark:bg-slate-800 h-2.5 rounded-full overflow-hidden">
                    <div class="h-full rounded-full ${progressColor} transition-all duration-500" style="width: ${Math.min(100, u.percentage)}%"></div>
                </div>
                <div class="flex justify-between text-[9px] text-slate-400 font-bold uppercase">
                    <span>Spent: ₹${u.spent}</span>
                    <span>Remaining: ₹${u.remaining}</span>
                </div>
            `;
            list.appendChild(card);
        });

    } catch (err) {
        console.error("Load budgets error", err);
    }
}

// Helper: Calculate daily suggested limit
function updateDailyGuideline(overall) {
    const field = document.getElementById("suggestedDailyLimit");
    if (!field) return;

    if (!overall || overall.budget === 0) {
        field.innerText = "₹0.00 / day";
        return;
    }

    const now = new Date();
    const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
    const remainingDays = Math.max(1, daysInMonth - now.getDate() + 1);

    const remainingBudget = Math.max(0.0, overall.remaining);
    const suggested = remainingBudget / remainingDays;

    field.innerText = `₹${suggested.toFixed(2)} / day`;
}

// Sum total spent today
async function loadTodaySpent() {
    const todayField = document.getElementById("spentToday");
    const statusField = document.getElementById("spentTodayStatus");
    if (!todayField) return;

    const todayStr = new Date().toISOString().split('T')[0];

    try {
        const res = await fetch(`/api/expenses?start_date=${todayStr}&end_date=${todayStr}`);
        if (!res.ok) return;
        const data = await res.json();

        const total = data.expenses.reduce((sum, item) => sum + item.amount, 0);
        todayField.innerText = `₹${total.toFixed(2)}`;
        statusField.innerText = `Logged ${data.expenses.length} transaction(s) today`;
    } catch (err) {
        console.error("Spent today calculation error", err);
    }
}
