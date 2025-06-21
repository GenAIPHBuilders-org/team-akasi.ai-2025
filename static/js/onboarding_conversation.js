// Onboarding Conversation JavaScript - Pure JavaScript Implementation

class ConversationController {
    constructor() {
        this.currentQuestion = 0;
        this.formData = {};
        this.conversationHistory = [];
        this.isProcessing = false;
        
        // Define the conversation flow
        this.questions = [
            {
                id: 'greeting',
                text: "Hello there! I'm Akasi, your AI health guardian. I'm excited to help you on your wellness journey! 😊 Let's start with the basics - what's your full name?",
                field: 'full_name',
                validation: (value) => value.trim().length >= 2
            },
            {
                id: 'date_of_birth',
                text: "Nice to meet you! Now, what's your date of birth? Please enter it in YYYY-MM-DD format.",
                field: 'date_of_birth',
                validation: (value) => {
                    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
                    return dateRegex.test(value) && !isNaN(Date.parse(value));
                }
            },
            {
                id: 'gender',
                text: "Thanks! What's your gender? You can choose from: Male, Female, Other, or Prefer not to say.",
                field: 'gender',
                validation: (value) => ['male', 'female', 'other', 'prefer not to say'].includes(value.toLowerCase())
            },
            {
                id: 'height',
                text: "Great! Now, what's your height in centimeters? (For example: 170)",
                field: 'height',
                validation: (value) => {
                    const height = parseFloat(value);
                    return !isNaN(height) && height >= 50 && height <= 300;
                }
            },
            {
                id: 'weight',
                text: "Perfect! What's your weight in kilograms? (For example: 70)",
                field: 'weight',
                validation: (value) => {
                    const weight = parseFloat(value);
                    return !isNaN(weight) && weight >= 20 && weight <= 500;
                }
            },
            {
                id: 'ethnicity',
                text: "Almost done! What's your ethnicity? You can choose from: Filipino, Chinese, Japanese, Korean, Indian, Caucasian, African Descent, Hispanic/Latino, Middle Eastern, Native American, Pacific Islander, Mixed Race, Other, or Prefer not to say.",
                field: 'ethnicity',
                validation: (value) => {
                    const validEthnicities = ['filipino', 'chinese', 'japanese', 'korean', 'indian', 'caucasian', 'african descent', 'hispanic/latino', 'middle eastern', 'native american', 'pacific islander', 'mixed race', 'other', 'prefer not to say'];
                    return validEthnicities.includes(value.toLowerCase());
                }
            }
        ];
        
        this.init();
    }

    init() {
        this.speechBubble = document.getElementById('akasi-speech-bubble');
        this.chatInput = document.getElementById('chat-input');
        this.sendButton = document.getElementById('send-button');
        this.chatHistoryButton = document.getElementById('chat-history-button');
        this.chatHistoryOverlay = document.getElementById('chat-history-overlay');
        this.closeChatHistory = document.getElementById('close-chat-history');
        this.chatMessages = document.getElementById('chat-messages');

        this.setupEventListeners();
        this.initializeChatHistory();
        this.startConversation();
    }

    initializeChatHistory() {
        // Clear any existing chat history for this session
        localStorage.removeItem('onboarding_chat_history');
        this.conversationHistory = [];
        
        // Add the initial Akasi message
        const initialMessage = "Hello there! I'm Akasi, your AI health guardian. I'm excited to help you on your wellness journey! 😊 Let's start with the basics - what's your full name?";
        this.addMessageToHistory('akasi', initialMessage);
    }

    addMessageToHistory(type, message) {
        const timestamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
        const messageEntry = {
            type: type, // 'akasi' or 'user'
            message: message,
            timestamp: timestamp
        };
        
        this.conversationHistory.push(messageEntry);
        
        // Save to localStorage
        localStorage.setItem('onboarding_chat_history', JSON.stringify(this.conversationHistory));
        
        // Update chat history modal in real-time if it's currently open
        this.updateChatHistoryIfOpen();
    }

    setupEventListeners() {
        // Send button click
        if (this.sendButton) {
            this.sendButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleSend();
            });
        }

        // Enter key in input
        if (this.chatInput) {
            this.chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleSend();
                }
            });

            // Auto-resize textarea
            this.chatInput.addEventListener('input', () => {
                this.chatInput.style.height = 'auto';
                this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 100) + 'px';
            });
        }

        // Chat history modal
        if (this.chatHistoryButton) {
            this.chatHistoryButton.addEventListener('click', () => this.showChatHistory());
        }

        if (this.closeChatHistory) {
            this.closeChatHistory.addEventListener('click', () => this.hideChatHistory());
        }

        if (this.chatHistoryOverlay) {
            this.chatHistoryOverlay.addEventListener('click', (e) => {
                if (e.target === this.chatHistoryOverlay) {
                    this.hideChatHistory();
                }
            });
        }

        // Form submission
        document.addEventListener('submit', async (e) => {
            if (e.target.id === 'personal-info-form') {
                e.preventDefault();
                await this.submitForm();
            }
        });

        // Add date input formatting for DD-MM-YYYY
        document.addEventListener('input', (e) => {
            if (e.target.id === 'dob' || e.target.name === 'date_of_birth') {
                this.formatDateInput(e.target);
            }
        });

        // Add date validation on blur
        document.addEventListener('blur', (e) => {
            if (e.target.id === 'dob' || e.target.name === 'date_of_birth') {
                const dateValue = e.target.value;
                if (dateValue && !this.validateDateFormat(dateValue)) {
                    e.target.style.borderColor = '#ef4444'; // red border
                    e.target.title = 'Please enter a valid date in DD-MM-YYYY format';
                } else {
                    e.target.style.borderColor = ''; // reset border
                    e.target.title = 'Please enter date in DD-MM-YYYY format';
                }
            }
        }, true);
    }

    startConversation() {
        // Initial message is already shown by server-side code
        // No need to duplicate it here - just ensure the speech bubble is visible
        if (this.speechBubble && !this.speechBubble.classList.contains('show')) {
            this.speechBubble.classList.add('show');
        }
    }

    showAkasiMessage(message) {
        if (this.speechBubble) {
            this.speechBubble.textContent = message;
            
            // Ensure the bubble is visible
            if (!this.speechBubble.classList.contains('show')) {
                this.speechBubble.classList.add('show');
            }

            // Store message in local chat history
            this.addMessageToHistory('akasi', message);
        } else {
            console.error('Speech bubble element not found!');
        }
    }

    showUserMessage(message) {
        // Store user message in local chat history
        this.addMessageToHistory('user', message);
        console.log('User message stored:', message);
    }

    async handleSend() {
        if (this.isProcessing) return;

        const userInput = this.chatInput.value.trim();
        if (!userInput) return;

        this.isProcessing = true;
        
        // Store the user input for processing
        const currentUserInput = userInput;
        
        // Clear the input immediately
        this.chatInput.value = '';
        this.chatInput.style.height = 'auto';
        
        // Store user message
        this.showUserMessage(currentUserInput);
        
        // Process the user's response
        await this.processUserResponse(currentUserInput);

        this.isProcessing = false;
    }

    async processUserResponse(userInput) {
        const currentQ = this.questions[this.currentQuestion];
        
        // Validate the response
        if (currentQ.validation && !currentQ.validation(userInput)) {
            this.showValidationError(currentQ.field);
            return;
        }

        // Store the response
        this.formData[currentQ.field] = userInput;

        // Move to next question
        this.currentQuestion++;

        // Show typing indicator
        this.showTypingIndicator();

        await this.delay(2000); // Increased from 1500ms to 2000ms for more realistic typing time

        if (this.currentQuestion < this.questions.length) {
            // Show next question
            this.showAkasiMessage(this.questions[this.currentQuestion].text);
        } else {
            // All questions answered, submit form
            this.showAkasiMessage("Perfect! I have all the information I need. Let me process this and set up your wellness journey...");
            
            await this.delay(2000);
            this.submitForm();
        }
    }

    showValidationError(field) {
        let errorMessage = "I'm sorry, that doesn't seem right. ";
        
        switch (field) {
            case 'full_name':
                errorMessage += "Please enter your full name (at least 2 characters).";
                break;
            case 'date_of_birth':
                errorMessage += "Please enter a valid date in YYYY-MM-DD format (e.g., 1990-05-15).";
                break;
            case 'gender':
                errorMessage += "Please choose from: Male, Female, Other, or Prefer not to say.";
                break;
            case 'height':
                errorMessage += "Please enter a valid height in centimeters (between 50-300 cm).";
                break;
            case 'weight':
                errorMessage += "Please enter a valid weight in kilograms (between 20-500 kg).";
                break;
            case 'ethnicity':
                errorMessage += "Please choose from the available ethnicity options I mentioned.";
                break;
            default:
                errorMessage += "Please check your input and try again.";
        }

        this.showAkasiMessage(errorMessage);
    }

    showTypingIndicator() {
        if (this.speechBubble) {
            this.speechBubble.innerHTML = `
                <div class="typing-indicator" style="display: flex;">
                    <span>Akasi is typing</span>
                    <div class="typing-dots">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            `;
            this.speechBubble.classList.add('show');
        }
    }

    async submitForm() {
        try {
            // Create form data for submission
            const formDataToSubmit = new FormData();
            
            // Map our stored data to the expected form fields
            formDataToSubmit.append('full_name', this.formData.full_name || '');
            formDataToSubmit.append('date_of_birth', this.formData.date_of_birth || '');
            formDataToSubmit.append('gender', this.formData.gender || '');
            formDataToSubmit.append('height', this.formData.height || '');
            formDataToSubmit.append('weight', this.formData.weight || '');
            formDataToSubmit.append('ethnicity', this.formData.ethnicity || '');

            // Submit to the server
            const response = await fetch('/onboarding/personal-info', {
                method: 'POST',
                body: formDataToSubmit
            });

            if (response.ok) {
                // Handle successful submission
                this.showAkasiMessage("Excellent! Your profile has been created successfully. Redirecting you to your wellness journal...");
                
                // Clear chat history after successful submission
                localStorage.removeItem('onboarding_chat_history');
                
                // Redirect after a short delay
                setTimeout(() => {
                    window.location.href = '/onboarding/wellness-journal';
                }, 3000);
            } else {
                throw new Error('Submission failed');
            }
        } catch (error) {
            console.error('Form submission error:', error);
            this.showAkasiMessage("I'm sorry, there was an issue saving your information. Please try again or contact support if the problem persists.");
            
            // Allow user to retry
            this.currentQuestion = this.questions.length - 1;
            this.isProcessing = false;
        }
    }

    renderChatHistory() {
        if (!this.chatMessages) return;

        // Load chat history from localStorage if available
        const storedHistory = localStorage.getItem('onboarding_chat_history');
        if (storedHistory) {
            this.conversationHistory = JSON.parse(storedHistory);
        }

        if (this.conversationHistory.length === 0) {
            this.chatMessages.innerHTML = `
                <div style="text-align: center; color: #9ca3af; padding: 2rem; font-style: italic;">
                    No conversation history yet. Start chatting to see your messages here!
                </div>
            `;
            return;
        }

        const messagesHTML = this.conversationHistory.map(entry => {
            const messageClass = entry.type === 'akasi' ? 'akasi-message' : 'user-message';
            return `
                <div class="chat-message">
                    <div class="${messageClass}">
                        ${entry.message}
                        <div class="message-time">${entry.timestamp}</div>
                    </div>
                </div>
            `;
        }).join('');

        this.chatMessages.innerHTML = messagesHTML;
    }

    showChatHistory() {
        if (this.chatHistoryOverlay) {
            // Render the chat history
            this.renderChatHistory();
            
            // Show the overlay with animation
            this.chatHistoryOverlay.style.display = 'block';
            // Force a reflow to ensure the display change takes effect
            this.chatHistoryOverlay.offsetHeight;
            // Add the show class for animation
            this.chatHistoryOverlay.classList.add('show');
            
            // Scroll to bottom after a short delay to allow messages to load
            setTimeout(() => {
                if (this.chatMessages) {
                    this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
                }
            }, 100);
        }
    }

    hideChatHistory() {
        if (this.chatHistoryOverlay) {
            // Remove show class for animation
            this.chatHistoryOverlay.classList.remove('show');
            
            // Hide after animation completes
            setTimeout(() => {
                this.chatHistoryOverlay.style.display = 'none';
            }, 300);
        }
    }

    updateChatHistoryIfOpen() {
        // Check if chat history modal is currently visible/open
        if (this.chatHistoryOverlay && 
            this.chatHistoryOverlay.style.display === 'block' && 
            this.chatHistoryOverlay.classList.contains('show')) {
            
            // Re-render the chat history to include the new message
            this.renderChatHistory();
            
            // Auto-scroll to bottom to show the latest message
            setTimeout(() => {
                if (this.chatMessages) {
                    this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
                }
            }, 50); // Small delay to ensure DOM update
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Add date validation for DD-MM-YYYY format
    validateDateFormat(dateString) {
        const datePattern = /^(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[0-2])-\d{4}$/;
        if (!datePattern.test(dateString)) {
            return false;
        }
        
        // Additional validation to check if the date is valid
        const parts = dateString.split('-');
        const day = parseInt(parts[0], 10);
        const month = parseInt(parts[1], 10);
        const year = parseInt(parts[2], 10);
        
        // Create a date object and check if it's valid
        const date = new Date(year, month - 1, day);
        return date.getFullYear() === year && 
               date.getMonth() === month - 1 && 
               date.getDate() === day;
    }

    // Format date input as user types
    formatDateInput(input) {
        let value = input.value.replace(/\D/g, ''); // Remove non-digits
        
        if (value.length >= 2) {
            value = value.substring(0, 2) + '-' + value.substring(2);
        }
        if (value.length >= 5) {
            value = value.substring(0, 5) + '-' + value.substring(5, 9);
        }
        
        input.value = value;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ConversationController();
});

// Also initialize if DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new ConversationController();
    });
} else {
    new ConversationController();
} 