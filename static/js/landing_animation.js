// static/js/landing_animation.js

document.addEventListener('DOMContentLoaded', (event) => {
    // Script for Landing Page Bubble
    const messages = [
        "Hello, I'm Akasi! 👋",
        "Your AI health guardian.",
        "Ready to get started?",
        "Let's track your wellness together!",
        "Sign up or log in below!"
    ];
    let messageIndex = 0;
    const messageElement = document.getElementById('akasi-message'); // Target landing page ID
    const changeInterval = 3500; // Time in milliseconds (3.5 seconds)
    const fadeDuration = 400; // Must match CSS transition duration

    function changeMessage() {
        if (!messageElement) return; // Exit if element not found

        // Fade out
        messageElement.classList.add('fade-out');

        // Wait for fade out, then change text and fade in
        setTimeout(() => {
            messageIndex = (messageIndex + 1) % messages.length; // Cycle through messages
            messageElement.textContent = messages[messageIndex];
            messageElement.classList.remove('fade-out'); // Fade in
        }, fadeDuration);
    }

    // Initial message set
    if (messageElement) {
        messageElement.textContent = messages[0];
        // Start the interval
         setInterval(changeMessage, changeInterval);
    } else {
        console.error("Akasi message element not found on landing page");
    }
});