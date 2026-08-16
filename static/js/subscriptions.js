// SpendIntel Subscriptions & Recurring Bills Frontend Logic

document.addEventListener('DOMContentLoaded', () => {
    loadSubscriptions();
    updateCurrencySymbols();

    const form = document.getElementById('subForm');
    if (form) {
        form.addEventListener('submit', handleSaveSubscription);
    }
});

function updateCurrencySymbols() {
    const symbol = window.CURRENT_CURRENCY || '₹';
    document.querySelectorAll('.currency-symbol').forEach(el => el.innerText = symbol);
}

let subscriptionsList = [];

async function loadSubscriptions() {
    try {
        const [subsRes, summaryRes] = await Promise.all([
            fetch('/api/subscriptions'),
            fetch('/api/subscriptions/summary')
        ]);

        subscriptionsList = await subsRes.json();
        const summary = await summaryRes.json();

        renderSubscriptions();
        renderSummary(summary);
    } catch (err) {
        console.error('Error loading subscriptions:', err);
    }
}

function renderSummary(summary) {
    const symbol = window.CURRENT_CURRENCY || '₹';
    document.getElementById('statMonthlyRunRate').innerText = `${symbol}${parseFloat(summary.monthly_run_rate || 0).toFixed(2)}`;
    document.getElementById('statYearlyCost').innerText = `${symbol}${parseFloat(summary.yearly_cost || 0).toFixed(2)}`;
    document.getElementById('statActiveCount').innerText = summary.active_count || 0;

    const banner = document.getElementById('renewalsAlertBanner');
    const upcoming = summary.upcoming_renewals || [];

    if (upcoming.length > 0) {
        banner.classList.remove('hidden');
        document.getElementById('renewalsAlertTitle').innerText = `${upcoming.length} Subscription(s) Renewing Soon!`;
        const names = upcoming.map(u => `${u.name} (${symbol}${u.amount})`).join(', ');
        document.getElementById('renewalsAlertText').innerText = `Upcoming in next 7 days: ${names}`;
    } else {
        banner.classList.add('hidden');
    }
}

function renderSubscriptions() {
    const symbol = window.CURRENT_CURRENCY || '₹';
    const container = document.getElementById('subscriptionsList');
    const empty = document.getElementById('emptySubsState');

    if (!subscriptionsList || subscriptionsList.length === 0) {
        container.innerHTML = '';
        empty.classList.remove('hidden');
        return;
    }

    empty.classList.add('hidden');
    container.innerHTML = '';

    const today = new Date();

    subscriptionsList.forEach(sub => {
        const card = document.createElement('div');
        card.className = "p-4 rounded-2xl bg-white dark:bg-darkCard border border-lightBorder dark:border-darkBorder shadow-xs flex items-center justify-between gap-4 transition-all hover:border-rose-500/30";

        // Calculate days remaining
        let daysLeftText = '';
        let badgeColor = 'bg-slate-100 dark:bg-slate-800 text-slate-500';
        if (sub.next_billing_date) {
            const nextDate = new Date(sub.next_billing_date);
            const diffTime = nextDate - today;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            if (diffDays <= 3 && diffDays >= 0) {
                daysLeftText = `Renews in ${diffDays} day${diffDays === 1 ? '' : 's'}!`;
                badgeColor = 'bg-amber-500/10 text-amber-500 border border-amber-500/20';
            } else if (diffDays < 0) {
                daysLeftText = `Overdue (${Math.abs(diffDays)}d ago)`;
                badgeColor = 'bg-rose-500/10 text-rose-500 border border-rose-500/20';
            } else {
                daysLeftText = `Renews in ${diffDays} days`;
                badgeColor = 'bg-blue-500/10 text-blue-500 border border-blue-500/20';
            }
        }

        card.innerHTML = `
            <div class="flex items-center gap-3.5">
                <div class="w-11 h-11 rounded-xl bg-rose-500/10 text-rose-500 flex items-center justify-center text-lg shrink-0">
                    <i class="${sub.icon || 'fa-solid fa-bell'}"></i>
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <h4 class="font-bold text-sm text-slate-900 dark:text-white">${escapeHtml(sub.name)}</h4>
                        <span class="text-[10px] font-bold px-2 py-0.5 rounded-full ${badgeColor}">${daysLeftText}</span>
                    </div>
                    <div class="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                        <span class="capitalize">${sub.billing_cycle}</span>
                        <span>•</span>
                        <span>Next: ${sub.next_billing_date || 'N/A'}</span>
                        ${sub.notes ? `<span>•</span> <span class="italic truncate max-w-[150px]">${escapeHtml(sub.notes)}</span>` : ''}
                    </div>
                </div>
            </div>

            <div class="flex items-center gap-4">
                <div class="text-right">
                    <span class="text-base font-extrabold text-slate-900 dark:text-white font-display">${symbol}${parseFloat(sub.amount).toFixed(2)}</span>
                    <span class="block text-[10px] text-slate-400 capitalize">${sub.billing_cycle}</span>
                </div>
                <button onclick="deleteSubscription(${sub.id})" class="p-2 text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 rounded-lg transition-all" title="Delete">
                    <i class="fa-solid fa-trash-can text-sm"></i>
                </button>
            </div>
        `;

        container.appendChild(card);
    });
}

function openSubModal() {
    document.getElementById('subModalTitle').innerText = 'Add Subscription';
    document.getElementById('subForm').reset();
    document.getElementById('subId').value = '';
    // Set default next billing date to 1 month ahead
    const nextMo = new Date();
    nextMo.setMonth(nextMo.getMonth() + 1);
    document.getElementById('subNextDate').value = nextMo.toISOString().split('T')[0];
    document.getElementById('subModal').classList.remove('hidden');
}

function closeSubModal() {
    document.getElementById('subModal')?.classList.add('hidden');
}

async function handleSaveSubscription(e) {
    e.preventDefault();
    const id = document.getElementById('subId').value;
    const name = document.getElementById('subName').value.trim();
    const amount = parseFloat(document.getElementById('subAmount').value);
    const billing_cycle = document.getElementById('subCycle').value;
    const next_billing_date = document.getElementById('subNextDate').value;
    const category = document.getElementById('subCategory').value;
    const notes = document.getElementById('subNotes').value.trim();

    const payload = { name, amount, billing_cycle, next_billing_date, category, notes };

    try {
        const url = id ? `/api/subscriptions/${id}` : '/api/subscriptions';
        const method = id ? 'PUT' : 'POST';
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            closeSubModal();
            loadSubscriptions();
        } else {
            const data = await res.json();
            alert('Error: ' + (data.error || 'Failed to save'));
        }
    } catch (err) {
        console.error(err);
        alert('Server error.');
    }
}

async function deleteSubscription(id) {
    if (!confirm('Are you sure you want to remove this subscription?')) return;
    try {
        const res = await fetch(`/api/subscriptions/${id}`, { method: 'DELETE' });
        if (res.ok) {
            loadSubscriptions();
        }
    } catch (err) {
        console.error(err);
    }
}

function escapeHtml(text) {
    if (!text) return '';
    return text.toString().replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
