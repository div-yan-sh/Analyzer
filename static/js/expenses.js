// Expenses Management Page Script

let currentPage = 1;
const limit = 10;

document.addEventListener("DOMContentLoaded", () => {
    updateCurrencySymbols();

    if (document.getElementById("expensesTableBody")) {
        loadExpenses();
        
        // Auto set default date in modal to today
        document.getElementById("expenseDate").value = new Date().toISOString().split('T')[0];

        // Check if openModal was requested in URL query
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('openModal') === '1') {
            openExpenseModal();
        }

        // Modal Form submission handler
        const expenseForm = document.getElementById("expenseForm");
        expenseForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const expId = document.getElementById("expenseId").value;
            const payload = {
                amount: parseFloat(document.getElementById("amount").value),
                description: document.getElementById("description").value,
                category: document.getElementById("category").value,
                subcategory: document.getElementById("subcategory").value,
                payment_method: document.getElementById("paymentMethod").value,
                expense_date: document.getElementById("expenseDate").value,
                is_essential: document.getElementById("isEssential").value === "true"
            };

            const url = expId ? `/api/expenses/${expId}` : '/api/expenses';
            const method = expId ? 'PUT' : 'POST';

            try {
                const res = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                
                if (res.ok) {
                    closeExpenseModal();
                    
                    if (data.anomaly_warning) {
                        alert(`🚨 ANOMALY ALERT:\n${data.anomaly_warning}`);
                    }
                    
                    loadExpenses();
                } else {
                    alert("Failed to save: " + (data.error || "Unknown error"));
                }
            } catch (err) {
                console.error("Form save error", err);
            }
        });
    }
});

function updateCurrencySymbols() {
    const symbol = window.CURRENT_CURRENCY || '₹';
    document.querySelectorAll('.currency-symbol').forEach(el => el.innerText = symbol);
}

// Load filtered and paginated expenses list
async function loadExpenses() {
    const symbol = window.CURRENT_CURRENCY || '₹';
    const tableBody = document.getElementById("expensesTableBody");
    if (!tableBody) return;

    tableBody.innerHTML = `<tr><td colspan="8" class="text-center py-8 text-slate-400">Loading expenses...</td></tr>`;

    // Compile filter query strings
    const search = document.getElementById("filterSearch").value;
    const category = document.getElementById("filterCategory").value;
    const payment = document.getElementById("filterPayment").value;
    const sortVal = document.getElementById("filterSort").value;
    const [sort_by, sort_order] = sortVal.split('-');
    
    const start_date = document.getElementById("filterStartDate").value;
    const end_date = document.getElementById("filterEndDate").value;
    const min_amount = document.getElementById("filterMinAmount").value;
    const max_amount = document.getElementById("filterMaxAmount").value;

    let url = `/api/expenses?page=${currentPage}&limit=${limit}&sort_by=${sort_by}&sort_order=${sort_order}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (category) url += `&category=${encodeURIComponent(category)}`;
    if (payment) url += `&payment_method=${encodeURIComponent(payment)}`;
    if (start_date) url += `&start_date=${start_date}`;
    if (end_date) url += `&end_date=${end_date}`;
    if (min_amount) url += `&min_amount=${min_amount}`;
    if (max_amount) url += `&max_amount=${max_amount}`;

    try {
        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();

        if (data.expenses.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-12 space-y-3">
                        <p class="text-slate-400 text-sm">Start tracking your expenses to unlock your spending analytics.</p>
                        <button onclick="openExpenseModal()" class="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow">Add Your First Expense</button>
                    </td>
                </tr>
            `;
            document.getElementById("pageInfo").innerText = "Showing 0 of 0 entries";
            document.getElementById("btnPrevPage").disabled = true;
            document.getElementById("btnNextPage").disabled = true;
            return;
        }

        tableBody.innerHTML = "";
        data.expenses.forEach(exp => {
            const tr = document.createElement("tr");
            tr.className = "hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors border-b border-lightBorder dark:border-darkBorder";
            
            const trDate = new Date(exp.expense_date).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' });
            const badgeType = exp.is_essential 
                ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400">Need</span>`
                : `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-800 dark:bg-indigo-950/40 dark:text-indigo-400 font-medium">Want</span>`;

            tr.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap text-xs text-slate-500 dark:text-slate-400">${trDate}</td>
                <td class="px-6 py-4 text-xs font-semibold text-slate-900 dark:text-white truncate max-w-[180px]">${escapeHtml(exp.description)}</td>
                <td class="px-6 py-4 whitespace-nowrap text-xs"><span class="px-2 py-0.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold">${exp.category}</span></td>
                <td class="px-6 py-4 whitespace-nowrap text-xs text-slate-500 dark:text-slate-400">${exp.subcategory || "-"}</td>
                <td class="px-6 py-4 whitespace-nowrap text-xs text-right font-bold text-slate-900 dark:text-white">${symbol}${exp.amount.toFixed(2)}</td>
                <td class="px-6 py-4 whitespace-nowrap text-xs text-slate-500 dark:text-slate-400">${exp.payment_method}</td>
                <td class="px-6 py-4 whitespace-nowrap text-xs">${badgeType}</td>
                <td class="px-6 py-4 whitespace-nowrap text-xs text-center space-x-1.5">
                    <button onclick="editExpense(${exp.id})" class="text-blue-600 dark:text-blue-400 hover:text-blue-800" title="Edit"><i class="fa-solid fa-pen-to-square"></i></button>
                    <button onclick="deleteExpense(${exp.id})" class="text-rose-500 hover:text-rose-700" title="Delete"><i class="fa-solid fa-trash"></i></button>
                </td>
            `;
            tableBody.appendChild(tr);
        });

        // Set pagination state
        const startEntry = (data.page - 1) * limit + 1;
        const endEntry = Math.min(data.page * limit, data.total);
        document.getElementById("pageInfo").innerText = `Showing ${startEntry}-${endEntry} of ${data.total} entries`;
        
        document.getElementById("btnPrevPage").disabled = !data.has_prev;
        document.getElementById("btnNextPage").disabled = !data.has_next;

    } catch (err) {
        console.error("Load expenses error", err);
    }
}

function escapeHtml(text) {
    if (!text) return '';
    return text.toString().replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// Pagination navigation
function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        loadExpenses();
    }
}

function nextPage() {
    currentPage++;
    loadExpenses();
}

function resetFilters() {
    document.getElementById("filterSearch").value = "";
    document.getElementById("filterCategory").value = "";
    document.getElementById("filterPayment").value = "";
    document.getElementById("filterSort").value = "expense_date-desc";
    document.getElementById("filterStartDate").value = "";
    document.getElementById("filterEndDate").value = "";
    document.getElementById("filterMinAmount").value = "";
    document.getElementById("filterMaxAmount").value = "";
    currentPage = 1;
    loadExpenses();
}

// Opening modals
function openExpenseModal(exp = null) {
    const modal = document.getElementById("expenseModal");
    const modalTitle = document.getElementById("modalTitle");
    const form = document.getElementById("expenseForm");

    modal.classList.remove("hidden");
    form.reset();

    if (exp) {
        modalTitle.innerText = "Edit Expense";
        document.getElementById("expenseId").value = exp.id;
        document.getElementById("amount").value = exp.amount;
        document.getElementById("description").value = exp.description;
        document.getElementById("category").value = exp.category;
        document.getElementById("subcategory").value = exp.subcategory;
        document.getElementById("paymentMethod").value = exp.payment_method;
        document.getElementById("expenseDate").value = exp.expense_date;
        document.getElementById("isEssential").value = exp.is_essential.toString();
    } else {
        modalTitle.innerText = "Add Expense";
        document.getElementById("expenseId").value = "";
        document.getElementById("expenseDate").value = new Date().toISOString().split('T')[0];
    }
}

function closeExpenseModal() {
    document.getElementById("expenseModal").classList.add("hidden");
}

// Fetch single record for editing
async function editExpense(id) {
    try {
        const res = await fetch(`/api/expenses`);
        if (!res.ok) return;
        const data = await res.json();
        const exp = data.expenses.find(e => e.id === id);
        
        if (exp) {
            openExpenseModal(exp);
        } else {
            alert("Record loaded.");
        }
    } catch (err) {
        console.error("Fetch editing error", err);
    }
}

// Delete Record
async function deleteExpense(id) {
    if (!confirm("Are you sure you want to delete this expense?")) return;
    
    try {
        const res = await fetch(`/api/expenses/${id}`, {
            method: 'DELETE'
        });
        if (res.ok) {
            loadExpenses();
        } else {
            alert("Failed to delete record.");
        }
    } catch (err) {
        console.error("Deletion error", err);
    }
}
