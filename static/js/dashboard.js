// Dashboard Operations

document.addEventListener("DOMContentLoaded", () => {
    updateCurrencySymbols();

    // Check if on dashboard page
    if (document.getElementById("statSpent")) {
        loadDashboardData();
        loadHealthScoreBadges();
        loadRecentExpenses();
    }

    // Quick Add Form handler
    const quickAddForm = document.getElementById("quickAddForm");
    if (quickAddForm) {
        quickAddForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const payload = {
                amount: parseFloat(document.getElementById("quickAmount").value),
                description: document.getElementById("quickDescription").value,
                category: document.getElementById("quickCategory").value,
                payment_method: document.getElementById("quickPaymentMethod").value,
                is_essential: document.getElementById("quickEssential").value === "true"
            };

            try {
                const res = await fetch('/api/expenses', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                
                if (res.ok) {
                    closeQuickAddModal();
                    
                    if (data.anomaly_warning) {
                        alert(`🚨 ANOMALY ALERT:\n${data.anomaly_warning}`);
                    }
                    
                    loadDashboardData();
                    loadHealthScoreBadges();
                    loadRecentExpenses();
                    quickAddForm.reset();
                } else {
                    alert("Error: " + (data.error || "Could not log expense."));
                }
            } catch (err) {
                console.error("Quick add failed", err);
            }
        });
    }
});

function updateCurrencySymbols() {
    const symbol = window.CURRENT_CURRENCY || '₹';
    document.querySelectorAll('.currency-symbol').forEach(el => el.innerText = symbol);
}

// Load Dashboard statistics summary
async function loadDashboardData() {
    const symbol = window.CURRENT_CURRENCY || '₹';
    try {
        const res = await fetch('/api/analytics/summary');
        if (!res.ok) return;
        const data = await res.json();

        // Populate cards
        document.getElementById("statSpent").innerText = `${symbol}${data.total_spent.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
        document.getElementById("statBudget").innerText = `${symbol}${data.budget.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
        document.getElementById("statDailyAvg").innerText = `${symbol}${data.daily_average.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
        document.getElementById("statPrediction").innerText = `${symbol}${data.predicted_spend.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
        
        // Update budget progress bar
        let pct = 0;
        if (data.budget > 0) {
            pct = Math.min(100, (data.total_spent / data.budget) * 100);
        }
        document.getElementById("statBudgetPercent").innerText = `${pct.toFixed(1)}%`;
        const bar = document.getElementById("statBudgetBar");
        bar.style.width = `${pct}%`;
        
        bar.className = "h-full rounded-full transition-all duration-500 ";
        if (pct < 60) bar.classList.add("bg-emerald-500");
        else if (pct < 80) bar.classList.add("bg-blue-500");
        else if (pct <= 100) bar.classList.add("bg-amber-500");
        else bar.classList.add("bg-rose-500");

        // Health Score gauge
        const score = data.health_score;
        document.getElementById("scoreText").innerText = score;
        document.getElementById("scoreRating").innerText = data.health_rating;

        // Circular dash array transition (circumference = 339.3)
        const circ = document.getElementById("scoreCirc");
        if (circ) {
            const offset = 339.3 - (score / 100) * 339.3;
            circ.style.strokeDashoffset = offset;
            
            circ.setAttribute("class", "transition-all duration-1000");
            if (score >= 85) circ.classList.add("text-emerald-500");
            else if (score >= 70) circ.classList.add("text-blue-500");
            else if (score >= 50) circ.classList.add("text-amber-500");
            else circ.classList.add("text-rose-500");
        }

        // Render In-App Notifications
        const alertsContainer = document.getElementById("alertsContainer");
        if (alertsContainer && data.alerts && data.alerts.length > 0) {
            alertsContainer.innerHTML = "";
            alertsContainer.classList.remove("hidden");
            data.alerts.forEach(alert => {
                const badge = document.createElement("div");
                badge.className = `p-3.5 rounded-xl border text-xs font-semibold flex items-center justify-between shadow-xs `;
                
                if (alert.type === "danger") {
                    badge.className += "bg-rose-50 border-rose-200 text-rose-800 dark:bg-rose-950/20 dark:border-rose-900 dark:text-rose-300";
                } else if (alert.type === "warning") {
                    badge.className += "bg-amber-50 border-amber-200 text-amber-800 dark:bg-amber-950/20 dark:border-amber-900 dark:text-amber-300";
                } else {
                    badge.className += "bg-emerald-50 border-emerald-200 text-emerald-800 dark:bg-emerald-950/20 dark:border-emerald-900 dark:text-emerald-300";
                }
                
                badge.innerHTML = `<span>${alert.message}</span><button onclick="this.parentElement.remove()" class="opacity-60 hover:opacity-100"><i class="fa-solid fa-xmark"></i></button>`;
                alertsContainer.appendChild(badge);
            });
        }

    } catch (err) {
        console.error("Failed to load dashboard statistics data", err);
    }
}

// Load Health Score & Gamification Badges
async function loadHealthScoreBadges() {
    try {
        const res = await fetch('/api/ai/health-score');
        if (!res.ok) return;
        const data = await res.json();
        const container = document.getElementById('badgesContainer');
        if (!container) return;

        container.innerHTML = '';
        (data.badges || []).forEach(badge => {
            const pill = document.createElement('div');
            pill.className = "flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-darkBg border border-lightBorder dark:border-darkBorder text-[11px] font-semibold text-slate-700 dark:text-slate-200 shadow-2xs hover:scale-105 transition-transform cursor-default";
            pill.title = badge.desc;
            pill.innerHTML = `<i class="${badge.icon} ${badge.color}"></i> <span>${badge.name}</span>`;
            container.appendChild(pill);
        });
    } catch (err) {
        console.error('Failed to load badges:', err);
    }
}

// Load 5 recent transactions
async function loadRecentExpenses() {
    const symbol = window.CURRENT_CURRENCY || '₹';
    try {
        const res = await fetch('/api/expenses?limit=5');
        if (!res.ok) return;
        const data = await res.json();
        const container = document.getElementById("recentExpensesList");
        
        if (!container) return;

        if (data.expenses.length === 0) {
            container.innerHTML = `<div class="py-6 text-center text-xs text-slate-400">No expenses logged this month yet.</div>`;
            return;
        }

        container.innerHTML = "";
        data.expenses.forEach(exp => {
            const item = document.createElement("div");
            item.className = "flex items-center justify-between py-2.5 transition-all hover:bg-slate-50/50 dark:hover:bg-slate-800/30 rounded-xl px-2";
            
            const icons = {
                "Food": "fa-utensils text-orange-500 bg-orange-500/10",
                "Transport": "fa-taxi text-blue-500 bg-blue-500/10",
                "Education": "fa-book text-emerald-500 bg-emerald-500/10",
                "Shopping": "fa-bag-shopping text-rose-500 bg-rose-500/10",
                "Entertainment": "fa-film text-purple-500 bg-purple-500/10",
                "Hostel/Rent": "fa-house text-slate-500 bg-slate-500/10",
                "Bills": "fa-bolt text-yellow-500 bg-yellow-500/10",
                "Health": "fa-heart-pulse text-red-500 bg-red-500/10",
                "Recharge": "fa-mobile-screen text-teal-500 bg-teal-500/10",
                "Travel": "fa-plane text-sky-500 bg-sky-500/10",
                "Other": "fa-receipt text-indigo-500 bg-indigo-500/10"
            };

            const iconClass = icons[exp.category] || "fa-receipt text-slate-500 bg-slate-500/10";
            const dateObj = new Date(exp.expense_date);
            const dateStr = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

            item.innerHTML = `
                <div class="flex items-center gap-3">
                    <span class="w-8 h-8 rounded-xl flex items-center justify-center text-xs ${iconClass.split(' ').slice(1).join(' ')}">
                        <i class="fa-solid ${iconClass.split(' ')[0]}"></i>
                    </span>
                    <div>
                        <h4 class="text-xs font-semibold text-slate-900 dark:text-white truncate max-w-[150px] sm:max-w-[250px]">${escapeHtml(exp.description)}</h4>
                        <span class="text-[10px] text-slate-400">${dateStr} • ${exp.category}</span>
                    </div>
                </div>
                <div class="text-right">
                    <span class="text-xs font-bold text-slate-900 dark:text-white">-${symbol}${exp.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                    <p class="text-[9px] text-slate-400">${exp.payment_method}</p>
                </div>
            `;
            container.appendChild(item);
        });

    } catch (err) {
        console.error("Failed to load recent expenses", err);
    }
}

function escapeHtml(text) {
    if (!text) return '';
    return text.toString().replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// Quick Add Modal toggling
function openQuickAddModal() {
    document.getElementById("quickAddModal").classList.remove("hidden");
}

function closeQuickAddModal() {
    document.getElementById("quickAddModal").classList.add("hidden");
}
