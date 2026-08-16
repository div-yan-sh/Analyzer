// SpendIntel Roommate & Group Bill Splitter Frontend Logic

document.addEventListener('DOMContentLoaded', () => {
    loadSplits();
    updateCurrencySymbols();
    
    // Add 2 initial member rows to the modal
    resetMemberRows();

    const form = document.getElementById('newSplitForm');
    if (form) {
        form.addEventListener('submit', handleCreateSplit);
    }
});

function updateCurrencySymbols() {
    const symbol = window.CURRENT_CURRENCY || '₹';
    document.querySelectorAll('.currency-symbol').forEach(el => el.innerText = symbol);
}

let splitsData = [];

async function loadSplits() {
    try {
        const res = await fetch('/api/splits');
        if (!res.ok) throw new Error('Failed to load');
        splitsData = await res.json();
        renderSplits();
        updateSummaryStats();
    } catch (err) {
        console.error('Error loading splits:', err);
    }
}

function updateSummaryStats() {
    const symbol = window.CURRENT_CURRENCY || '₹';
    const active = splitsData.filter(s => !s.settled);
    const settled = splitsData.filter(s => s.settled);

    let pendingTotal = 0;
    active.forEach(s => {
        (s.members || []).forEach(m => {
            if (!m.has_paid) pendingTotal += parseFloat(m.share_amount || 0);
        });
    });

    document.getElementById('statActiveSplits').innerText = active.length;
    document.getElementById('statPendingAmount').innerText = `${symbol}${pendingTotal.toFixed(2)}`;
    document.getElementById('statSettledCount').innerText = settled.length;
}

function renderSplits() {
    const symbol = window.CURRENT_CURRENCY || '₹';
    const grid = document.getElementById('splitsGrid');
    const empty = document.getElementById('emptySplitsState');

    if (!splitsData || splitsData.length === 0) {
        grid.innerHTML = '';
        empty.classList.remove('hidden');
        return;
    }

    empty.classList.add('hidden');
    grid.innerHTML = '';

    splitsData.forEach(split => {
        const card = document.createElement('div');
        card.className = "bg-white dark:bg-darkCard p-5 rounded-2xl border border-lightBorder dark:border-darkBorder shadow-sm space-y-4 flex flex-col justify-between";

        const members = split.members || [];
        const paidCount = members.filter(m => m.has_paid).length;
        const totalMembers = members.length;
        const progressPct = totalMembers > 0 ? (paidCount / totalMembers) * 100 : 0;

        let membersHtml = members.map(m => `
            <div class="flex items-center justify-between p-2 rounded-xl bg-slate-50 dark:bg-darkBg/60 text-xs">
                <div class="flex items-center gap-2">
                    <button onclick="toggleMemberPaid(${split.id}, ${m.id})" class="w-5 h-5 rounded-full flex items-center justify-center transition-all ${m.has_paid ? 'bg-emerald-500 text-white' : 'border-2 border-slate-300 dark:border-slate-600 text-transparent hover:border-emerald-500'}">
                        <i class="fa-solid fa-check text-[10px]"></i>
                    </button>
                    <span class="font-medium text-slate-800 dark:text-slate-200 ${m.has_paid ? 'line-through text-slate-400 dark:text-slate-500' : ''}">${escapeHtml(m.name)}</span>
                </div>
                <div class="flex items-center gap-2">
                    <span class="font-semibold ${m.has_paid ? 'text-emerald-500' : 'text-slate-700 dark:text-slate-300'}">${symbol}${parseFloat(m.share_amount).toFixed(2)}</span>
                    ${split.upi_id && !m.has_paid ? `
                        <button onclick="showUpiQr('${split.upi_id}', '${escapeHtml(split.paid_by)}', ${m.share_amount}, '${escapeHtml(split.title)}')" class="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/20 text-[10px] font-bold" title="Generate UPI QR">
                            <i class="fa-solid fa-qrcode"></i> Pay
                        </button>
                    ` : ''}
                </div>
            </div>
        `).join('');

        card.innerHTML = `
            <div class="space-y-3">
                <div class="flex items-start justify-between gap-2">
                    <div>
                        <h4 class="font-bold text-base text-slate-900 dark:text-white">${escapeHtml(split.title)}</h4>
                        <span class="text-xs text-slate-400">Paid by <b class="text-slate-700 dark:text-slate-300">${escapeHtml(split.paid_by)}</b></span>
                    </div>
                    <div class="text-right">
                        <span class="text-lg font-extrabold text-slate-900 dark:text-white font-display">${symbol}${parseFloat(split.total_amount).toFixed(2)}</span>
                        <div>
                            ${split.settled ? 
                                '<span class="inline-block text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">Settled</span>' : 
                                '<span class="inline-block text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500 border border-amber-500/20">Pending</span>'
                            }
                        </div>
                    </div>
                </div>

                <!-- Progress -->
                <div class="space-y-1">
                    <div class="flex justify-between text-[11px] text-slate-400 font-semibold">
                        <span>Settlement Progress</span>
                        <span>${paidCount}/${totalMembers} paid</span>
                    </div>
                    <div class="w-full bg-slate-100 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
                        <div class="bg-emerald-500 h-full rounded-full transition-all duration-300" style="width: ${progressPct}%"></div>
                    </div>
                </div>

                <!-- Members List -->
                <div class="space-y-1.5 pt-1">
                    ${membersHtml}
                </div>
            </div>

            <!-- Card Actions -->
            <div class="flex items-center justify-between pt-3 border-t border-lightBorder dark:border-darkBorder text-xs text-slate-400">
                <span>${split.created_at ? new Date(split.created_at).toLocaleDateString() : ''}</span>
                <button onclick="deleteSplit(${split.id})" class="text-rose-500 hover:text-rose-600 p-1 hover:bg-rose-50 dark:hover:bg-rose-950/30 rounded-lg transition-all" title="Delete Split">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            </div>
        `;

        grid.appendChild(card);
    });
}

// Dynamic Members Row in Modal
function resetMemberRows() {
    const list = document.getElementById('membersInputsList');
    if (!list) return;
    list.innerHTML = `
        <div class="member-row grid grid-cols-12 gap-2 items-center">
            <input type="text" placeholder="Name (e.g. You / Payer)" value="You" required class="col-span-7 px-3 py-1.5 rounded-xl border border-lightBorder dark:border-darkBorder bg-slate-50 dark:bg-darkBg text-slate-900 dark:text-white text-xs member-name">
            <input type="number" step="0.01" placeholder="Share (₹)" required class="col-span-4 px-3 py-1.5 rounded-xl border border-lightBorder dark:border-darkBorder bg-slate-50 dark:bg-darkBg text-slate-900 dark:text-white text-xs member-share">
            <div class="col-span-1 text-center text-slate-400"><i class="fa-solid fa-lock text-[10px]"></i></div>
        </div>
        <div class="member-row grid grid-cols-12 gap-2 items-center">
            <input type="text" placeholder="Roommate 1" value="Roommate 1" required class="col-span-7 px-3 py-1.5 rounded-xl border border-lightBorder dark:border-darkBorder bg-slate-50 dark:bg-darkBg text-slate-900 dark:text-white text-xs member-name">
            <input type="number" step="0.01" placeholder="Share (₹)" required class="col-span-4 px-3 py-1.5 rounded-xl border border-lightBorder dark:border-darkBorder bg-slate-50 dark:bg-darkBg text-slate-900 dark:text-white text-xs member-share">
            <button type="button" onclick="this.closest('.member-row').remove(); recalculateEqualShares();" class="col-span-1 text-rose-400 hover:text-rose-600 text-xs"><i class="fa-solid fa-xmark"></i></button>
        </div>
    `;
    recalculateEqualShares();
}

function addSplitMemberRow() {
    const list = document.getElementById('membersInputsList');
    const rowCount = list.querySelectorAll('.member-row').length + 1;
    const row = document.createElement('div');
    row.className = "member-row grid grid-cols-12 gap-2 items-center";
    row.innerHTML = `
        <input type="text" placeholder="Roommate ${rowCount}" value="Roommate ${rowCount}" required class="col-span-7 px-3 py-1.5 rounded-xl border border-lightBorder dark:border-darkBorder bg-slate-50 dark:bg-darkBg text-slate-900 dark:text-white text-xs member-name">
        <input type="number" step="0.01" placeholder="Share (₹)" required class="col-span-4 px-3 py-1.5 rounded-xl border border-lightBorder dark:border-darkBorder bg-slate-50 dark:bg-darkBg text-slate-900 dark:text-white text-xs member-share">
        <button type="button" onclick="this.closest('.member-row').remove(); recalculateEqualShares();" class="col-span-1 text-rose-400 hover:text-rose-600 text-xs"><i class="fa-solid fa-xmark"></i></button>
    `;
    list.appendChild(row);
    recalculateEqualShares();
}

function recalculateEqualShares() {
    const totalAmount = parseFloat(document.getElementById('splitTotalAmount').value) || 0;
    const rows = document.querySelectorAll('.member-row');
    if (rows.length === 0 || totalAmount <= 0) return;

    const equalShare = (totalAmount / rows.length).toFixed(2);
    rows.forEach(row => {
        const shareInput = row.querySelector('.member-share');
        if (shareInput) shareInput.value = equalShare;
    });
}

// Open / Close Modals
function openNewSplitModal() {
    document.getElementById('newSplitModal')?.classList.remove('hidden');
    resetMemberRows();
}

function closeNewSplitModal() {
    document.getElementById('newSplitModal')?.classList.add('hidden');
}

async function handleCreateSplit(e) {
    e.preventDefault();
    const title = document.getElementById('splitTitle').value.trim();
    const total_amount = parseFloat(document.getElementById('splitTotalAmount').value);
    const paid_by = document.getElementById('splitPaidBy').value.trim();
    const upi_id = document.getElementById('splitUpiId').value.trim();

    const memberRows = document.querySelectorAll('.member-row');
    const members = [];
    memberRows.forEach(row => {
        const name = row.querySelector('.member-name').value.trim();
        const share = parseFloat(row.querySelector('.member-share').value) || 0;
        if (name) {
            members.push({
                name: name,
                share_amount: share,
                has_paid: (name.toLowerCase() === paid_by.toLowerCase() || name.toLowerCase() === 'you')
            });
        }
    });

    try {
        const res = await fetch('/api/splits', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, total_amount, paid_by, upi_id, members })
        });
        const data = await res.json();
        if (res.ok) {
            closeNewSplitModal();
            loadSplits();
        } else {
            alert('Failed to create split: ' + (data.error || 'Unknown error'));
        }
    } catch (err) {
        console.error(err);
        alert('Server error creating split.');
    }
}

async function toggleMemberPaid(splitId, memberId) {
    try {
        const res = await fetch(`/api/splits/${splitId}/member/${memberId}/toggle`, {
            method: 'POST'
        });
        if (res.ok) {
            loadSplits();
        }
    } catch (err) {
        console.error(err);
    }
}

async function deleteSplit(splitId) {
    if (!confirm('Are you sure you want to delete this group split?')) return;
    try {
        const res = await fetch(`/api/splits/${splitId}`, { method: 'DELETE' });
        if (res.ok) {
            loadSplits();
        }
    } catch (err) {
        console.error(err);
    }
}

async function showUpiQr(upiId, paidBy, amount, title) {
    const symbol = window.CURRENT_CURRENCY || '₹';
    try {
        const res = await fetch(`/api/splits/upi-link?upi_id=${encodeURIComponent(upiId)}&name=${encodeURIComponent(paidBy)}&amount=${amount}&note=${encodeURIComponent(title)}`);
        const data = await res.json();
        if (res.ok) {
            document.getElementById('upiQrImage').src = data.qr_image_url;
            document.getElementById('upiPayeeName').innerText = paidBy;
            document.getElementById('upiPayeeId').innerText = upiId;
            document.getElementById('upiAmount').innerText = `${symbol}${parseFloat(amount).toFixed(2)}`;
            document.getElementById('upiDeepLinkBtn').href = data.upi_uri;
            document.getElementById('upiQrModal').classList.remove('hidden');
        }
    } catch (err) {
        console.error(err);
    }
}

function closeUpiQrModal() {
    document.getElementById('upiQrModal')?.classList.add('hidden');
}

function escapeHtml(text) {
    if (!text) return '';
    return text.toString().replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
