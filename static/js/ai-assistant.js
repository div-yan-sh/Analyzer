// AI Financial Assistant Chats Handler

let chatHistory = [];

document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chatForm");
    if (chatForm) {
        chatForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const input = document.getElementById("chatInput");
            const msgText = input.value.trim();
            if (!msgText) return;

            input.value = "";
            await sendMessage(msgText);
        });
    }
});

// Sends message to API and handles bubble generation
async function sendMessage(text) {
    const chatWindow = document.getElementById("chatWindow");
    if (!chatWindow) return;

    // 1. Add student message bubble to UI
    appendMessageBubble("student", text);
    scrollChat();

    // 2. Disable form inputs while responding
    const input = document.getElementById("chatInput");
    const submitBtn = document.querySelector("#chatForm button");
    input.disabled = true;
    submitBtn.disabled = true;

    // Add a loading placeholder bubble
    const loadingId = appendLoadingBubble();
    scrollChat();

    // 3. Dispatch POST request to API
    try {
        const res = await fetch('/api/ai/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                history: chatHistory
            })
        });
        const data = await res.json();
        
        // Remove loading indicator
        document.getElementById(loadingId).remove();

        if (res.ok) {
            // 4. Add assistant response to UI
            appendMessageBubble("assistant", data.response);
            
            // 5. Update local history array
            chatHistory.push({ role: "student", content: text });
            chatHistory.push({ role: "assistant", content: data.response });
        } else {
            appendMessageBubble("assistant", "Sorry, I am having trouble connecting to my brain right now. Please try again.");
        }
    } catch (err) {
        console.error("Chat dispatch error", err);
        document.getElementById(loadingId) && document.getElementById(loadingId).remove();
        appendMessageBubble("assistant", "Connection error. Please check your network.");
    } finally {
        input.disabled = false;
        submitBtn.disabled = false;
        input.focus();
        scrollChat();
    }
}

// Visual appends for speech bubbles
function appendMessageBubble(role, content) {
    const chatWindow = document.getElementById("chatWindow");
    const bubble = document.createElement("div");
    
    const isStudent = role === "student";
    
    if (isStudent) {
        bubble.className = "flex gap-3 max-w-[85%] ml-auto justify-end";
        bubble.innerHTML = `
            <div class="bg-blue-600 text-white p-4 rounded-2xl rounded-tr-none shadow-sm text-sm">
                <p class="leading-relaxed">${content}</p>
            </div>
            <div class="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-600 flex items-center justify-center flex-shrink-0 font-bold text-xs">
                U
            </div>
        `;
    } else {
        bubble.className = "flex gap-3 max-w-[85%]";
        bubble.innerHTML = `
            <div class="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-500 flex items-center justify-center flex-shrink-0 text-sm">
                <i class="fa-solid fa-robot"></i>
            </div>
            <div class="bg-white dark:bg-darkCard border border-lightBorder dark:border-darkBorder p-4 rounded-2xl rounded-tl-none shadow-sm text-sm text-slate-700 dark:text-slate-300">
                <p class="leading-relaxed">${content}</p>
            </div>
        `;
    }
    
    chatWindow.appendChild(bubble);
}

// Appends temporary loading animations
function appendLoadingBubble() {
    const chatWindow = document.getElementById("chatWindow");
    const loadingId = "loader_" + Date.now();
    const bubble = document.createElement("div");
    bubble.id = loadingId;
    bubble.className = "flex gap-3 max-w-[85%]";
    bubble.innerHTML = `
        <div class="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-500 flex items-center justify-center flex-shrink-0 text-sm">
            <i class="fa-solid fa-robot animate-bounce"></i>
        </div>
        <div class="bg-white dark:bg-darkCard border border-lightBorder dark:border-darkBorder px-4 py-3 rounded-2xl rounded-tl-none shadow-sm text-sm text-slate-400">
            <div class="flex items-center gap-1">
                <span class="w-1.5 h-1.5 rounded-full bg-slate-400 animate-pulse"></span>
                <span class="w-1.5 h-1.5 rounded-full bg-slate-400 animate-pulse delay-75"></span>
                <span class="w-1.5 h-1.5 rounded-full bg-slate-400 animate-pulse delay-150"></span>
            </div>
        </div>
    `;
    chatWindow.appendChild(bubble);
    return loadingId;
}

// Helper: scroll to bottom
function scrollChat() {
    const chatWindow = document.getElementById("chatWindow");
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Trigger query chip clicks programmatically
function sendQuickMessage(text) {
    sendMessage(text);
}
