document.addEventListener('DOMContentLoaded', function() {
    const messageElement = document.getElementById('wellness-message');
    
    // Show wellness messages directly
    if (window.wellnessMessages) {
        messageElement.innerHTML = window.wellnessMessages.join('<br>');
    }
    
    // No animation needed - everything is already on screen
});