// Insights and AI Report Scripts

document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("anomaliesList")) {
        loadAnomalies();
        loadRecommendations();
    }
});

// Load Z-score anomalies
async function loadAnomalies() {
    const list = document.getElementById("anomaliesList");
    if (!list) return;

    try {
        const res = await fetch('/api/anomalies');
        if (!res.ok) return;
        const data = await res.json();

        if (data.length === 0) {
            list.innerHTML = `
                <div class="py-6 text-center text-xs text-slate-400 flex flex-col items-center gap-2">
                    <span class="w-10 h-10 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center"><i class="fa-solid fa-circle-check"></i></span>
                    <span>Excellent! No unusual spending patterns detected.</span>
                </div>
            `;
            return;
        }

        list.innerHTML = "";
        data.forEach(anom => {
            const dateObj = new Date(anom.expense_date);
            const dateStr = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
            
            const div = document.createElement("div");
            div.className = "py-4 space-y-1";
            div.innerHTML = `
                <div class="flex justify-between items-baseline">
                    <span class="px-2 py-0.5 rounded bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400 text-[10px] font-bold uppercase">${anom.category} Anomaly</span>
                    <span class="text-xs text-slate-400">${dateStr}</span>
                </div>
                <div class="flex justify-between items-baseline gap-2">
                    <h4 class="text-xs font-semibold text-slate-900 dark:text-white truncate max-w-[250px]">${anom.description}</h4>
                    <span class="text-xs font-bold text-rose-500">-₹${anom.amount.toFixed(2)}</span>
                </div>
                <p class="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">${anom.reason}</p>
            `;
            list.appendChild(div);
        });

    } catch (err) {
        console.error("Load anomalies error", err);
    }
}

// Load local recommendation cards
async function loadRecommendations() {
    const list = document.getElementById("recommendationsList");
    if (!list) return;

    try {
        const res = await fetch('/api/insights');
        if (!res.ok) return;
        const data = await res.json();

        list.innerHTML = "";
        data.forEach(rec => {
            const div = document.createElement("div");
            div.className = "py-4 space-y-2";
            
            let badgeColor = "bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-400";
            if (rec.type === "danger") {
                badgeColor = "bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-400";
            } else if (rec.type === "warning") {
                badgeColor = "bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400";
            } else if (rec.type === "success") {
                badgeColor = "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400";
            }

            div.innerHTML = `
                <div class="flex justify-between items-center">
                    <span class="px-2.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider ${badgeColor}">${rec.type}</span>
                </div>
                <h4 class="text-xs font-bold text-slate-900 dark:text-white leading-tight">${rec.title}</h4>
                <p class="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">${rec.content}</p>
            `;
            list.appendChild(div);
        });

    } catch (err) {
        console.error("Load recommendations error", err);
    }
}

// Call AI API to generate monthly executive summary
async function generateAIReport() {
    const btn = document.getElementById("btnGenerateReport");
    if (!btn) return;

    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner animate-spin"></i> Running Statistical Models...`;

    try {
        const res = await fetch('/api/ai/monthly-report', { method: 'POST' });
        const report = await res.json();

        if (res.ok) {
            document.getElementById("reportSummary").innerText = report.summary;
            
            // Render observations list
            const obsContainer = document.getElementById("reportObservations");
            obsContainer.innerHTML = "";
            report.key_observations.forEach(o => {
                const li = document.createElement("li");
                li.className = "text-xs text-slate-600 dark:text-slate-400 list-disc ml-4 leading-relaxed";
                li.innerText = o;
                obsContainer.appendChild(li);
            });

            // Render warnings list
            const warnContainer = document.getElementById("reportWarnings");
            warnContainer.innerHTML = "";
            report.warnings.forEach(w => {
                const li = document.createElement("li");
                li.className = "text-xs text-rose-500 dark:text-rose-400 list-disc ml-4 leading-relaxed font-semibold";
                li.innerText = w;
                warnContainer.appendChild(li);
            });

            // Render recommendations list
            const recContainer = document.getElementById("reportRecommendations");
            recContainer.innerHTML = "";
            report.recommendations.forEach(r => {
                const li = document.createElement("li");
                li.className = "text-xs text-slate-600 dark:text-slate-400 list-disc ml-4 leading-relaxed";
                li.innerText = r;
                recContainer.appendChild(li);
            });

            // Reveal section
            document.getElementById("aiReportSection").classList.remove("hidden");
        } else {
            alert("AI report service temporarily rate-limited. Falling back to local report.");
        }
    } catch (err) {
        console.error("AI Report generation failed", err);
        alert("Unable to reach AI services.");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-sparkles"></i> Generate AI Monthly Report`;
    }
}
