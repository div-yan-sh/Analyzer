// SpendIntel AI Smart Receipt Scanner Frontend Logic
let currentImageFile = null;
let currentImageBase64 = null;

document.addEventListener('DOMContentLoaded', () => {
    setupDropZone();
    updateCurrencySymbols();
});

function updateCurrencySymbols() {
    const symbol = window.CURRENT_CURRENCY || '₹';
    document.querySelectorAll('.currency-symbol').forEach(el => el.innerText = symbol);
}

function setupDropZone() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('receiptFileInput');

    if (!dropZone || !fileInput) return;

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('border-blue-500', 'bg-blue-500/10');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('border-blue-500', 'bg-blue-500/10');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            handleSelectedFile(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleSelectedFile(e.target.files[0]);
        }
    });
}

function handleSelectedFile(file) {
    if (!file.type.startsWith('image/')) {
        alert('Please upload a valid image file (JPG, PNG, WebP).');
        return;
    }

    currentImageFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        currentImageBase64 = e.target.result;
        document.getElementById('receiptImagePreview').src = currentImageBase64;
        document.getElementById('imagePreviewContainer').classList.remove('hidden');
        document.getElementById('uploadPlaceholder').classList.add('hidden');
        document.getElementById('btnScanAction').removeAttribute('disabled');
    };
    reader.readAsDataURL(file);
}

function clearReceiptUpload() {
    currentImageFile = null;
    currentImageBase64 = null;
    const fileInput = document.getElementById('receiptFileInput');
    if (fileInput) fileInput.value = '';
    
    document.getElementById('receiptImagePreview').src = '';
    document.getElementById('imagePreviewContainer').classList.add('hidden');
    document.getElementById('uploadPlaceholder').classList.remove('hidden');
    document.getElementById('btnScanAction').setAttribute('disabled', 'true');
    document.getElementById('scanLine').classList.add('hidden');
}

async function processReceiptImage() {
    if (!currentImageFile && !currentImageBase64) {
        alert('Please select or drag an image first.');
        return;
    }

    const btn = document.getElementById('btnScanAction');
    const scanLine = document.getElementById('scanLine');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing with Gemini Vision...';
    scanLine.classList.remove('hidden');

    try {
        const formData = new FormData();
        if (currentImageFile) {
            formData.append('file', currentImageFile);
        } else if (currentImageBase64) {
            formData.append('image_base64', currentImageBase64);
        }

        const res = await fetch('/api/ai/scan-receipt', {
            method: 'POST',
            body: currentImageFile ? formData : JSON.stringify({ image_base64: currentImageBase64 }),
            headers: currentImageFile ? {} : { 'Content-Type': 'application/json' }
        });

        const result = await res.json();
        if (result.success && result.data) {
            displayExtractedReceipt(result.data);
        } else {
            alert('Failed to extract data: ' + (result.error || 'Unknown error'));
        }
    } catch (err) {
        console.error('Scan failed:', err);
        alert('Error connecting to Gemini Vision service.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-bolt"></i> Scan with Gemini Vision';
        scanLine.classList.add('hidden');
    }
}

async function loadSampleReceipt(sampleId) {
    try {
        const res = await fetch('/api/ai/sample-receipts');
        const samples = await res.json();
        const found = samples.find(s => s.id === sampleId);
        if (found) {
            displayExtractedReceipt(found);
        }
    } catch (err) {
        console.error('Failed to load sample:', err);
    }
}

function displayExtractedReceipt(data) {
    const symbol = window.CURRENT_CURRENCY || '₹';
    document.getElementById('emptyResultState').classList.add('hidden');
    document.getElementById('scannedExpenseForm').classList.remove('hidden');
    document.getElementById('saveActionContainer').classList.remove('hidden');

    // Highlights
    const total = parseFloat(data.total_amount || 0);
    document.getElementById('displayTotalAmount').innerText = `${symbol}${total.toFixed(2)}`;
    document.getElementById('displayMerchant').innerText = data.merchant || 'Unknown Store';

    // Editable Inputs
    document.getElementById('extractedMerchant').value = data.merchant || '';
    document.getElementById('extractedAmount').value = total.toFixed(2);
    document.getElementById('extractedCategory').value = data.category || 'Food';
    document.getElementById('extractedSubcategory').value = data.subcategory || '';
    document.getElementById('extractedDate').value = data.date || new Date().toISOString().split('T')[0];
    document.getElementById('extractedPaymentMethod').value = data.payment_method || 'UPI';

    // Confidence Pill
    const conf = Math.round((data.confidence || 0.95) * 100);
    const confPill = document.getElementById('confidencePill');
    const confText = document.getElementById('confidenceText');
    confPill.classList.remove('hidden');
    confText.innerText = `${conf}% OCR Accuracy`;

    // Line Items Breakdown Table
    const tbody = document.getElementById('extractedItemsTableBody');
    tbody.innerHTML = '';
    const items = data.items || [];
    document.getElementById('itemsCount').innerText = `${items.length} items found`;

    if (items.length > 0) {
        items.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="px-3 py-2 font-medium">${escapeHtml(item.name || 'Item')}</td>
                <td class="px-3 py-2 text-center text-slate-400">${item.qty || 1}</td>
                <td class="px-3 py-2 text-right font-semibold">${symbol}${parseFloat(item.price || 0).toFixed(2)}</td>
            `;
            tbody.appendChild(tr);
        });
    } else {
        tbody.innerHTML = `<tr><td colspan="3" class="px-3 py-2 text-center text-slate-400 italic">No itemized lines detected</td></tr>`;
    }
}

async function saveExtractedExpense() {
    const merchant = document.getElementById('extractedMerchant').value.trim();
    const amount = parseFloat(document.getElementById('extractedAmount').value);
    const category = document.getElementById('extractedCategory').value;
    const subcategory = document.getElementById('extractedSubcategory').value.trim();
    const expense_date = document.getElementById('extractedDate').value;
    const payment_method = document.getElementById('extractedPaymentMethod').value;

    if (!merchant || isNaN(amount) || amount <= 0) {
        alert('Please provide a valid merchant description and amount.');
        return;
    }

    const btn = document.getElementById('btnConfirmSave');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';

    try {
        const payload = {
            description: merchant,
            amount: amount,
            category: category,
            subcategory: subcategory,
            expense_date: expense_date,
            payment_method: payment_method,
            is_essential: ['Food', 'Education', 'Bills', 'Hostel/Rent', 'Health'].includes(category)
        };

        const res = await fetch('/api/expenses', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok) {
            alert('Receipt successfully logged to your Expenses!');
            window.location.href = '/expenses';
        } else {
            alert('Error saving: ' + (data.error || 'Unknown error'));
        }
    } catch (err) {
        console.error('Save failed:', err);
        alert('Could not save expense. Please check your connection.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-check"></i> Confirm & Save to Expenses';
    }
}

function escapeHtml(text) {
    if (!text) return '';
    return text.toString().replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
