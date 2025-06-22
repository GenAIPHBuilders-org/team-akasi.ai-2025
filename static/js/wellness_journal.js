// Wellness Journal Base JavaScript - Speech Bubble Integration

// Speech bubble specific utilities
function resetSpeechBubbleToDefault() {
    const speechContent = document.getElementById('akasi-speech-content');
    if (speechContent) {
        speechContent.innerHTML = `
            <div class="akasi-speech-text">
                Hi there! I'm Akasi, your personal wellness assistant. I help you track your health by building a wellness journal. I've activated my body scanner to check how you're doing. Just start by telling me how you feel today. You can also add notes, symptoms, photos, or any medical documents along the way. Let's begin!
            </div>
        `;
        console.log("Speech bubble reset to default message");
    }
}

// Handle speech bubble errors gracefully
function handleSpeechBubbleError(errorMessage) {
    const speechContent = document.getElementById('akasi-speech-content');
    if (speechContent) {
        speechContent.innerHTML = `
            <div class="akasi-speech-text error-message">
                ${errorMessage || "I'm having trouble right now. Please try again."}
            </div>
        `;
        console.log("Speech bubble showing error:", errorMessage);
    }
}

// Show speech bubble thinking state manually (if needed)
function showSpeechBubbleThinking() {
    const speechContent = document.getElementById('akasi-speech-content');
    if (speechContent) {
        speechContent.innerHTML = `
            <div class="typing-indicator-content">
                <span class="typing-text">Akasi is thinking</span>
                <div class="typing-dots">
                    <span class="typing-dot dot-1"></span>
                    <span class="typing-dot dot-2"></span>
                    <span class="typing-dot dot-3"></span>
                </div>
            </div>
        `;
        speechContent.className = 'akasi-speech-text typing-indicator';
        console.log("Speech bubble showing thinking state");
    }
}

// Basic initialization - reduced functionality since main features moved to wellness_enhancements.js
document.addEventListener('DOMContentLoaded', () => {
    console.log("Wellness journal speech bubble integration ready");
    
    // Add global error handlers for speech bubble
    window.addEventListener('unhandledrejection', (event) => {
        console.error('Unhandled promise rejection in speech bubble:', event.reason);
        // Don't show error in speech bubble for all unhandled rejections
        // Only specific ones should trigger this
    });
});

// Export utilities for use by other scripts
window.WellnessJournal = {
    resetSpeechBubbleToDefault,
    handleSpeechBubbleError,
    showSpeechBubbleThinking
};
