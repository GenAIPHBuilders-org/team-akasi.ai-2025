// Wellness Journal Base JavaScript - Minimal functionality

// Utility functions for wellness journal
function autoResizeTextarea(textarea) {
    if (!textarea) return;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.max(textarea.scrollHeight, parseInt(getComputedStyle(textarea).minHeight, 10) || 44)}px`;
}

// Setup basic chat input functionality
function setupBasicChatInput() {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('input', () => autoResizeTextarea(chatInput));
        
        // Enter key for submission (Shift+Enter for new line)
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const form = chatInput.closest('form');
                if (form) {
                    // Let HTMX handle the form submission
                    form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
                }
            }
        });
    }
}

// Basic initialization
document.addEventListener('DOMContentLoaded', () => {
    setupBasicChatInput();
    console.log("Wellness journal base functionality initialized");
});

// Export for use by other scripts
window.WellnessJournal = {
    autoResizeTextarea,
    setupBasicChatInput
};
