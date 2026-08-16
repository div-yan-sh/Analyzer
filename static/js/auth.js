// Authentication and Profile Operations

document.addEventListener("DOMContentLoaded", () => {
    // Register form handler
    const registerForm = document.getElementById("registerForm");
    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const submitBtn = document.getElementById("submitBtn");
            const alertBox = document.getElementById("alertBox");
            
            submitBtn.disabled = true;
            submitBtn.innerText = "Creating Account...";
            showAlert(alertBox, null); // Hide alert

            const payload = {
                name: document.getElementById("name").value,
                email: document.getElementById("email").value,
                password: document.getElementById("password").value,
                college: document.getElementById("college").value,
                year: parseInt(document.getElementById("year").value),
                course: document.getElementById("course").value,
                monthly_income_or_allowance: parseFloat(document.getElementById("allowance").value)
            };

            try {
                const res = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                
                if (res.ok) {
                    showAlert(alertBox, "success", "Registration successful! Redirecting...");
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 1200);
                } else {
                    showAlert(alertBox, "danger", data.error || "Registration failed.");
                    submitBtn.disabled = false;
                    submitBtn.innerText = "Create Account";
                }
            } catch (err) {
                showAlert(alertBox, "danger", "Network error. Please try again.");
                submitBtn.disabled = false;
                submitBtn.innerText = "Create Account";
            }
        });
    }

    // Login form handler
    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const submitBtn = document.getElementById("submitBtn");
            const alertBox = document.getElementById("alertBox");

            submitBtn.disabled = true;
            submitBtn.innerText = "Logging in...";
            showAlert(alertBox, null);

            const payload = {
                email: document.getElementById("email").value,
                password: document.getElementById("password").value,
                remember: document.getElementById("remember").checked
            };

            try {
                const res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                
                if (res.ok) {
                    showAlert(alertBox, "success", "Login successful! Redirecting...");
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 1000);
                } else {
                    showAlert(alertBox, "danger", data.error || "Invalid credentials.");
                    submitBtn.disabled = false;
                    submitBtn.innerText = "Log In";
                }
            } catch (err) {
                showAlert(alertBox, "danger", "Network error. Please try again.");
                submitBtn.disabled = false;
                submitBtn.innerText = "Log In";
            }
        });
    }

    // Profile update form handler
    const profileForm = document.getElementById("profileForm");
    if (profileForm) {
        profileForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const alertBox = document.getElementById("profileAlertBox");
            showAlert(alertBox, null);

            const payload = {
                name: document.getElementById("profName").value,
                monthly_income_or_allowance: parseFloat(document.getElementById("profAllowance").value),
                college: document.getElementById("profCollege").value,
                year: parseInt(document.getElementById("profYear").value),
                course: document.getElementById("profCourse").value
            };

            const password = document.getElementById("profPassword").value;
            if (password) {
                payload.password = password;
            }

            try {
                const res = await fetch('/api/user/profile', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                
                if (res.ok) {
                    showAlert(alertBox, "success", "Profile updated successfully!");
                    document.getElementById("profPassword").value = ""; // clear field
                } else {
                    showAlert(alertBox, "danger", data.error || "Profile update failed.");
                }
            } catch (err) {
                showAlert(alertBox, "danger", "Network error.");
            }
        });
    }
});

// Helper alert visual function
function showAlert(box, type, msg) {
    if (!box) return;
    if (!type) {
        box.classList.add("hidden");
        return;
    }
    box.classList.remove("hidden", "bg-emerald-50", "text-emerald-700", "border-emerald-200", "bg-rose-50", "text-rose-700", "border-rose-200");
    if (type === "success") {
        box.classList.add("bg-emerald-50", "text-emerald-700", "border-emerald-200");
    } else {
        box.classList.add("bg-rose-50", "text-rose-700", "border-rose-200");
    }
    box.innerText = msg;
}

// Data Export Trigger
async function exportData(format) {
    try {
        const res = await fetch('/api/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ format: format })
        });
        if (res.ok) {
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `student_expenses_backup.${format}`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } else {
            alert("Failed to export data.");
        }
    } catch (err) {
        console.error("Export error", err);
    }
}

// Clear / Reset All User Data Trigger
async function resetData() {
    const confirmation1 = confirm("⚠ DANGER: Are you sure you want to delete all transactions, budgets, and goals? This action CANNOT be undone!");
    if (!confirmation1) return;
    const confirmation2 = confirm("Please confirm once more. This will permanently wipe your expense logs.");
    if (!confirmation2) return;

    try {
        const res = await fetch('/api/user/reset', { method: 'POST' });
        if (res.ok) {
            alert("All account records have been reset successfully.");
            window.location.reload();
        } else {
            alert("Data reset operation failed.");
        }
    } catch (err) {
        console.error("Reset error", err);
    }
}
