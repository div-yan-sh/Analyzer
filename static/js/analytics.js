// Analytics Dashboard Scripts

let chartDaily = null;
let chartCategory = null;
let chartPayment = null;
let chartEssential = null;
let chartMonthlyBar = null;

let selectedDays = 30;

document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("chartDaily")) {
        setTimeline(30); // Default to 30 days
        loadMonthlyBarChart();
        loadMoMComparison();
    }
});

// Switch timelines
function setTimeline(days) {
    selectedDays = days;
    
    // Toggle active classes on buttons
    [7, 30, 90, 180].forEach(d => {
        const btn = document.getElementById(`btnTimeline${d}`);
        if (d === days) {
            btn.className = "px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 text-white transition-all duration-200";
        } else {
            btn.className = "px-3.5 py-1.5 text-xs font-semibold rounded-lg hover:text-slate-950 dark:hover:text-white transition-all duration-200 text-slate-500 dark:text-slate-400";
        }
    });

    loadDailyTrendChart(days);
    loadDistributionCharts(days);
}

// Fetch daily totals and render line chart
async function loadDailyTrendChart(days) {
    try {
        const res = await fetch(`/api/analytics/trends?days=${days}`);
        if (!res.ok) return;
        const data = await res.json();

        const labels = data.map(item => {
            const date = new Date(item.date);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });
        const totals = data.map(item => item.total);

        const ctx = document.getElementById("chartDaily").getContext("2d");
        
        if (chartDaily) {
            chartDaily.destroy();
        }

        const isDark = document.documentElement.classList.contains('dark');
        const gridColor = isDark ? '#1F293D' : '#E2E8F0';
        const textColor = isDark ? '#94A3B8' : '#64748B';

        chartDaily = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Daily Spent (₹)',
                    data: totals,
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointRadius: days > 30 ? 0 : 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { color: gridColor },
                        ticks: { color: textColor, font: { size: 10 } }
                    },
                    y: {
                        grid: { color: gridColor },
                        ticks: { color: textColor, font: { size: 10 } }
                    }
                }
            }
        });

    } catch (err) {
        console.error("Daily trend error", err);
    }
}

// Fetch distributions and render doughnut & pie charts
async function loadDistributionCharts(days) {
    try {
        // Calculate start date based on days selected
        const start = new Date();
        start.setDate(start.getDate() - days);
        const start_date = start.toISOString().split('T')[0];

        const res = await fetch(`/api/analytics/categories?start_date=${start_date}`);
        if (!res.ok) return;
        const data = await res.json();

        const isDark = document.documentElement.classList.contains('dark');
        const textColor = isDark ? '#94A3B8' : '#64748B';

        // 1. Category Doughnut
        const catLabels = Object.keys(data.categories);
        const catValues = Object.values(data.categories);
        const catCtx = document.getElementById("chartCategory").getContext("2d");
        if (chartCategory) chartCategory.destroy();
        
        chartCategory = new Chart(catCtx, {
            type: 'doughnut',
            data: {
                labels: catLabels,
                datasets: [{
                    data: catValues,
                    backgroundColor: [
                        '#F59E0B', '#3B82F6', '#10B981', '#EC4899', '#8B5CF6', 
                        '#64748B', '#F59E0B', '#EF4444', '#14B8A6', '#0EA5E9', '#6366F1'
                    ],
                    borderWidth: isDark ? 2 : 1,
                    borderColor: isDark ? '#151C2C' : '#FFFFFF'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: textColor, font: { size: 10 } }
                    }
                }
            }
        });

        // 2. Payment Method Doughnut
        const pmLabels = Object.keys(data.payment_methods);
        const pmValues = Object.values(data.payment_methods);
        const pmCtx = document.getElementById("chartPayment").getContext("2d");
        if (chartPayment) chartPayment.destroy();

        chartPayment = new Chart(pmCtx, {
            type: 'doughnut',
            data: {
                labels: pmLabels,
                datasets: [{
                    data: pmValues,
                    backgroundColor: ['#6366F1', '#10B981', '#F59E0B', '#EF4444', '#3B82F6', '#64748B'],
                    borderWidth: isDark ? 2 : 1,
                    borderColor: isDark ? '#151C2C' : '#FFFFFF'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: textColor, font: { size: 10 } }
                    }
                }
            }
        });

        // 3. Essential vs Non-essential Pie
        const essCtx = document.getElementById("chartEssential").getContext("2d");
        if (chartEssential) chartEssential.destroy();

        chartEssential = new Chart(essCtx, {
            type: 'pie',
            data: {
                labels: ['Essential (Needs)', 'Non-Essential (Wants)'],
                datasets: [{
                    data: [data.essential_vs_non_essential.essential, data.essential_vs_non_essential.non_essential],
                    backgroundColor: ['#10B981', '#6366F1'],
                    borderWidth: isDark ? 2 : 1,
                    borderColor: isDark ? '#151C2C' : '#FFFFFF'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: textColor, font: { size: 10 } }
                    }
                }
            }
        });

    } catch (err) {
        console.error("Distribution charts error", err);
    }
}

// Fetch historical monthly totals (Bar chart)
async function loadMonthlyBarChart() {
    try {
        const res = await fetch('/api/analytics/monthly');
        if (!res.ok) return;
        const data = await res.json();

        const labels = data.map(item => item.label);
        const totals = data.map(item => item.total);

        const ctx = document.getElementById("chartMonthlyBar").getContext("2d");
        if (chartMonthlyBar) chartMonthlyBar.destroy();

        const isDark = document.documentElement.classList.contains('dark');
        const gridColor = isDark ? '#1F293D' : '#E2E8F0';
        const textColor = isDark ? '#94A3B8' : '#64748B';

        chartMonthlyBar = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Monthly Total (₹)',
                    data: totals,
                    backgroundColor: '#6366F1',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: textColor, font: { size: 10 } }
                    },
                    y: {
                        grid: { color: gridColor },
                        ticks: { color: textColor, font: { size: 10 } }
                    }
                }
            }
        });

    } catch (err) {
        console.error("Monthly bar error", err);
    }
}

// Load month-over-month category comparisons list
async function loadMoMComparison() {
    const list = document.getElementById("comparisonList");
    if (!list) return;

    try {
        // Fetch current categories
        const now = new Date();
        const firstOfCurrent = new Date(now.getFullYear(), now.month, 1).toISOString().split('T')[0];
        const resCurr = await fetch(`/api/analytics/categories?start_date=${firstOfCurrent}`);
        
        // Fetch previous categories
        const firstOfPrev = new Date(now.getFullYear(), now.month - 1, 1).toISOString().split('T')[0];
        const resPrev = await fetch(`/api/analytics/categories?start_date=${firstOfPrev}&end_date=${firstOfCurrent}`);

        if (!resCurr.ok || !resPrev.ok) return;

        const dataCurr = await resCurr.json();
        const dataPrev = await resPrev.json();

        const categories = Array.from(new Set([
            ...Object.keys(dataCurr.categories),
            ...Object.keys(dataPrev.categories)
        ]));

        if (categories.length === 0) {
            list.innerHTML = `<div class="py-6 text-center text-xs text-slate-400">Not enough history to compare yet.</div>`;
            return;
        }

        list.innerHTML = "";
        categories.forEach(cat => {
            const valCurr = dataCurr.categories[cat] || 0.0;
            const valPrev = dataPrev.categories[cat] || 0.0;

            if (valCurr === 0 && valPrev === 0) return;

            let pctChangeStr = "";
            let pctClass = "";
            let arrow = "";

            if (valPrev > 0) {
                const pct = ((valCurr - valPrev) / valPrev) * 100;
                if (pct > 0) {
                    pctChangeStr = `+${pct.toFixed(1)}%`;
                    pctClass = "text-rose-500 font-bold";
                    arrow = `<i class="fa-solid fa-arrow-trend-up text-rose-500"></i>`;
                } else if (pct < 0) {
                    pctChangeStr = `${pct.toFixed(1)}%`;
                    pctClass = "text-emerald-500 font-bold";
                    arrow = `<i class="fa-solid fa-arrow-trend-down text-emerald-500"></i>`;
                } else {
                    pctChangeStr = "0.0%";
                    pctClass = "text-slate-400";
                    arrow = `<i class="fa-solid fa-arrows-left-right text-slate-400"></i>`;
                }
            } else {
                pctChangeStr = "New";
                pctClass = "text-blue-500 font-bold";
                arrow = `<i class="fa-solid fa-star text-blue-500 text-[10px]"></i>`;
            }

            const div = document.createElement("div");
            div.className = "flex items-center justify-between py-2 text-xs";
            div.innerHTML = `
                <div class="flex items-center gap-2">
                    ${arrow}
                    <span class="font-semibold text-slate-700 dark:text-slate-300">${cat}</span>
                </div>
                <div class="text-right">
                    <span class="text-slate-500">₹${valPrev.toFixed(0)} &rarr; ₹${valCurr.toFixed(0)}</span>
                    <span class="ml-2 ${pctClass}">${pctChangeStr}</span>
                </div>
            `;
            list.appendChild(div);
        });

    } catch (err) {
        console.error("Comparison MoM error", err);
    }
}
