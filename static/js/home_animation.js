// static/js/home_animation.js

// Script for Home Page Bubble - Assumes homeMessages is defined globally by an inline script

document.addEventListener('DOMContentLoaded', (event) => {
    // Check if the messages array exists (defined inline in HTML)
    if (typeof window.homeMessages === 'undefined' || !Array.isArray(window.homeMessages)) {
        console.error("Home page messages array (window.homeMessages) not found or invalid.");
        return;
    }

    let homeMessageIndex = 0;
    const homeMessageElement = document.getElementById('akasi-message-home'); // Target home page ID
    const homeChangeInterval = 4000; // Slightly longer interval?
    const homeFadeDuration = 400; // Must match CSS transition duration

    function changeHomeMessage() {
        if (!homeMessageElement) return;
        homeMessageElement.classList.add('fade-out');
        setTimeout(() => {
            homeMessageIndex = (homeMessageIndex + 1) % window.homeMessages.length; // Use the global array
            homeMessageElement.textContent = window.homeMessages[homeMessageIndex];
            homeMessageElement.classList.remove('fade-out');
        }, homeFadeDuration);
    }

    if (homeMessageElement) {
        // Set initial message from the global array
        homeMessageElement.textContent = window.homeMessages[0];
        setInterval(changeHomeMessage, homeChangeInterval);
    } else {
        console.error("Akasi home message element not found");
    }
});