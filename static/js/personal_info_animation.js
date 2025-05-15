document.addEventListener('DOMContentLoaded', function() {
    const greetingElement = document.getElementById('greeting-message');
    const showFormButton = document.getElementById('show-form-button');
    const form = document.getElementById('personal-info-form');
    const confirmButton = document.getElementById('confirm-personal-info');
    
    // Show greeting messages directly
    if (window.greetingMessages) {
        greetingElement.innerHTML = window.greetingMessages.join('<br>');
    }
    
    // Show form button click
    showFormButton.addEventListener('click', function() {
        showFormButton.style.display = 'none';
        form.style.display = 'block';
        form.style.opacity = '1';
    });
    
    // Confirm button click
    confirmButton.addEventListener('click', function() {
        window.location.href = '/onboarding/wellness-journal';
    });
});