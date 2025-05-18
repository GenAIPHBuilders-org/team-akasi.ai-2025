// --- SVG Icon Definitions are now embedded directly in JS where needed ---

// --- UTILITY FUNCTIONS ---
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;
    const toastId = `toast-${Date.now()}`;
    let alertClass = 'alert-info';
    if (type === 'success') alertClass = 'alert-success';
    if (type === 'error') alertClass = 'alert-error';
    if (type === 'warning') alertClass = 'alert-warning';

    const toastHTML = `
        <div id="${toastId}" class="alert ${alertClass} shadow-lg animate-fadeIn">
            <span>${message}</span>
        </div>
    `;
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    setTimeout(() => {
        const toastElement = document.getElementById(toastId);
        if (toastElement) {
            toastElement.classList.remove('animate-fadeIn');
            toastElement.style.transition = 'opacity 0.5s ease-out';
            toastElement.style.opacity = '0';
            setTimeout(() => toastElement.remove(), 500);
        }
    }, 3000);
}

// --- GLOBAL STATE (Simplified) ---
let chatMessages = [];
let stagedAttachments = [];
let journalIssues = [];
let scanPosition = 0;
let scanDirection = 'down';
let isScanning = true;
let selectedPartId = null;
let isAnalyzing = false;
let isBodyGlowing = false;
let isGeneratingDiaryLoading = false;
let scanAnimationInterval = null;
let bodyGlowTimeout = null;

const bodyParts = [
    { id: 'HEAD', label: 'Head', position: 12, keywords: ['head', 'headache', 'migraine', 'brain', 'skull', 'concussion'], description: 'The head houses the brain and major sensory organs. Common issues include headaches, migraines, and tension.' },
    { id: 'EYES', label: 'Eyes', position: 16, keywords: ['eye', 'vision', 'sight', 'blind', 'blur', 'see'], description: 'Eyes are complex sensory organs responsible for vision. Common issues include strain, dryness, and blurred vision.' },
    { id: 'EARS', label: 'Ears', position: 18, keywords: ['ear', 'hearing', 'deaf', 'audio', 'earache', 'eardrum'], description: 'Ears are responsible for hearing and balance. Common issues include infections, tinnitus, and hearing loss.' },
    { id: 'NECK', label: 'Neck', position: 22, keywords: ['neck', 'throat', 'swallow', 'thyroid', 'cervical'], description: 'The neck supports the head and enables movement. Common issues include stiffness, pain, and strain from poor posture.' },
    { id: 'SHOULDER', label: 'Shoulders', position: 30, keywords: ['shoulder', 'rotator', 'cuff', 'collar', 'scapula'], description: 'Shoulders are complex joints with wide range of motion. Common issues include rotator cuff injuries, frozen shoulder, and dislocation.' },
    { id: 'CHEST', label: 'Chest', position: 35, keywords: ['chest', 'breast', 'rib', 'pectoral', 'lung', 'heart', 'sternum', 'lungs', 'cough'], description: 'The chest houses vital organs including the heart and lungs. Common issues include pain, tightness, and respiratory concerns.' },
    { id: 'BACK', label: 'Back', position: 40, keywords: ['back', 'spine', 'posture', 'vertebra', 'lumbar'], description: 'The back includes the spine and supporting muscles. Common issues include lower back pain, sciatica, and muscle strain.' },
    { id: 'TORSO', label: 'Torso', position: 50, keywords: ['torso', 'abdomen', 'stomach', 'belly', 'gut', 'core', 'digestion', 'appetite'], description: 'The torso houses vital organs and core muscles. Common issues include digestive problems and core weakness.' },
    { id: 'ARMS', label: 'Arms', position: 40, keywords: ['arm', 'elbow', 'bicep', 'tricep', 'forearm', 'upper arm', 'humerus'], description: 'Arms include multiple joints and muscles. Common issues include sprains, tennis elbow, and carpal tunnel syndrome.' },
    { id: 'HANDS', label: 'Hands', position: 60, keywords: ['hand', 'wrist', 'finger', 'palm', 'knuckle', 'thumb'], description: 'Hands are complex structures for precise movements. Common issues include arthritis, carpal tunnel, and tendonitis.' },
    { id: 'HIPS', label: 'Hips', position: 70, keywords: ['hip', 'pelvis', 'groin', 'pelvic', 'iliac'], description: 'Hips are weight-bearing joints that connect the legs to the torso. Common issues include arthritis, bursitis, and impingement.' },
    { id: 'LEGS', label: 'Legs', position: 80, keywords: ['leg', 'thigh', 'hamstring', 'quad', 'calf', 'shin', 'femur', 'tibia'], description: 'Legs include several major muscle groups and joints. Common issues include muscle strains, knee pain, and shin splints.' },
    { id: 'KNEES', label: 'Knees', position: 85, keywords: ['knee', 'patella', 'acl', 'mcl', 'meniscus', 'joint'], description: 'Knees are complex hinge joints. Common issues include ACL tears, arthritis, and runner\'s knee.' },
    { id: 'FEET', label: 'Feet', position: 95, keywords: ['foot', 'feet', 'ankle', 'toe', 'heel', 'arch', 'sole'], description: 'Feet are complex structures that bear weight. Common issues include plantar fasciitis, bunions, and arch problems.' }
];

// --- DOM Elements (to be assigned in initializeApp) ---
let messagesArea, chatInput, sendButton, attachmentButton, attachmentOptionsContent, fileInput, stagedAttachmentsContainer, messagesEndRef;
let clearChatButton, addAIBubbleButton, addUserBubbleButton, attachImageButton, attachDocumentButton;
let bodyScannerSvg, scanLineGroup, scanLine, scanLineHighlightRect, selectedPartHighlightGroup, selectedPartHighlightCircle;
let scannerStatusText, scannerStatusIconContainer, scannerStatusContainer;
let debugStartScanButton, debugStopScanButton, debugNarrowScanButton, debugFullBodyGlowButton, restartScanButton, finishJournalButton;
let journalEntriesList, noJournalEntriesDiv, noJournalIconContainer, clearJournalContainer, clearAllJournalButton, addManualEntryButton;
let narrowScanModal, closeNarrowScanModalButton, narrowScanInput, confirmNarrowScanButton;
let manualEntryModal, manualEntryForm, manualTitleInput, manualStatusSelect, manualSummaryTextarea, manualDateInput;
let cancelManualEntryButton, saveManualEntryButton, closeManualEntryModalButton;
let diaryLoadingOverlay, diaryLoadingIconContainer;


// --- CHATBOX LOGIC ---
function renderMessages() {
    if (!messagesArea) return; 
    messagesArea.innerHTML = ''; 
    chatMessages.forEach((msg, index) => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('flex', 'animate-fadeIn'); 
        messageDiv.style.animationDelay = \`\${index * 70}ms\`;

        if (msg.sender === 'user') {
            messageDiv.classList.add('justify-end');
        } else {
            messageDiv.classList.add('justify-start');
        }

        let attachmentsHTML = '';
        if (msg.attachments && msg.attachments.length > 0) {
            attachmentsHTML = \`<div class="mt-2 pt-2 space-y-2 \${msg.text ? 'border-t' : ''} \${msg.sender === 'user' ? 'border-green-400/50' : 'border-gray-300/70'}">\`;
            msg.attachments.forEach(att => {
                attachmentsHTML += \`
                    <div class="p-1.5 rounded-md bg-base-100/50 border border-base-300/50 flex items-center gap-2">\`;
                if (att.type === 'image' && att.url) {
                    attachmentsHTML += \`
                        <div>
                            <img src="\${att.url}" alt="\${att.name || 'Attached image'}" class="rounded max-w-full h-auto max-h-32 object-contain" onerror="this.onerror=null; this.src='https://placehold.co/100x75/FEE2E2/DC2626?text=Error';">
                            <p class="text-xs text-base-content/70 mt-1 truncate">\${att.name} (\${att.size})</p>
                        </div>\`;
                } else if (att.type === 'document') {
                    // CORRECTED: Embed SVG string directly for paperclip
                    attachmentsHTML += \`
                        <div class="flex items-center gap-2">
                            <span class="text-primary flex-shrink-0"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-primary"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg></span>
                            <div class="flex-grow overflow-hidden">
                                <p class="text-xs font-medium text-base-content/90 truncate">\${att.name}</p>
                                <p class="text-xs text-base-content/70">\${att.size}</p>
                            </div>
                        </div>\`;
                }
                attachmentsHTML += \`</div>\`;
            });
            attachmentsHTML += \`</div>\`;
        }

        const bubbleRounding = (msg.attachments && msg.attachments.length > 0) ?
                               (msg.sender === 'user' ? 'rounded-b-xl' : 'rounded-b-xl') :
                               (msg.sender === 'user' ? 'rounded-br-none' : 'rounded-bl-none');
        
        // CORRECTED: Embed SVG strings directly for user and bot icons
        const avatarIconHTML = msg.sender === 'user' ? 
            '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-white"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>' : 
            '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-primary-content"><rect x="3" y="11" width="18" height="10" rx="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path><line x1="10" y1="16" x2="10.01" y2="16"></line><line x1="14" y1="16" x2="14.01" y2="16"></line></svg>';

        messageDiv.innerHTML = \`
            <div class="flex items-end max-w-xs sm:max-w-md md:max-w-lg \${msg.sender === 'user' ? 'flex-row-reverse' : ''}">
                <div class="avatar placeholder p-0 w-8 h-8 rounded-full \${msg.sender === 'user' ? 'ml-2 user-message-gradient' : 'mr-2 bg-base-300'}">
                    <div class="bg-transparent rounded-full w-8 h-8 flex items-center justify-center">
                        \${avatarIconHTML}
                    </div>
                </div>
                <div class="chat-bubble \${msg.sender === 'user' ? 'chat-bubble-primary user-message-gradient' : 'chat-bubble-neutral bg-base-300 text-base-content'} \${bubbleRounding} shadow-md">
                    \${msg.text ? \`<p class="text-sm leading-relaxed chat-message-text">\${msg.text}</p>\` : ''}
                    \${attachmentsHTML}
                </div>
            </div>
        \`;
        messagesArea.appendChild(messageDiv);
    });
    if (messagesEndRef) messagesEndRef.scrollIntoView({ behavior: 'smooth' });
}

// ... (Rest of your JavaScript functions: handleSendMessage, autoResizeTextarea, file handling,
//      renderStagedAttachments, removeStagedAttachment, debug handlers, modal handlers,
//      journal logic, scanner logic, etc. adapted similarly)


// --- INITIALIZATION ---
function initializeApp() {
    // Assign DOM elements to global variables
    messagesArea = document.getElementById('messagesArea');
    chatInput = document.getElementById('chatInput');
    sendButton = document.getElementById('sendButton');
    attachmentButton = document.getElementById('attachmentButton');
    attachmentOptionsContent = document.getElementById('attachmentOptionsContent');
    fileInput = document.getElementById('fileInput');
    stagedAttachmentsContainer = document.getElementById('stagedAttachmentsContainer');
    messagesEndRef = document.getElementById('messagesEndRef');
    clearChatButton = document.getElementById('clearChatButton');
    addAIBubbleButton = document.getElementById('addAIBubbleButton');
    addUserBubbleButton = document.getElementById('addUserBubbleButton');
    attachImageButton = document.getElementById('attachImageButton');
    attachDocumentButton = document.getElementById('attachDocumentButton');

    bodyScannerSvg = document.getElementById('bodyScannerSvg');
    scanLineGroup = document.getElementById('scanLineGroup');
    scanLine = document.getElementById('scanLine');
    scanLineHighlightRect = document.getElementById('scanLineHighlight');
    selectedPartHighlightGroup = document.getElementById('selectedPartHighlightGroup');
    selectedPartHighlightCircle = document.getElementById('selectedPartHighlightCircle');
    scannerStatusText = document.getElementById('scannerStatusText');
    scannerStatusIconContainer = document.getElementById('scannerStatusIconContainer');
    scannerStatusContainer = document.getElementById('scannerStatusContainer');

    debugStartScanButton = document.getElementById('debugStartScanButton');
    debugStopScanButton = document.getElementById('debugStopScanButton');
    debugNarrowScanButton = document.getElementById('debugNarrowScanButton');
    debugFullBodyGlowButton = document.getElementById('debugFullBodyGlowButton');
    restartScanButton = document.getElementById('restartScanButton');
    finishJournalButton = document.getElementById('finishJournalButton');
    
    journalEntriesList = document.getElementById('journalEntriesList');
    noJournalEntriesDiv = document.getElementById('noJournalEntries');
    noJournalIconContainer = document.getElementById('noJournalIconContainer');
    clearJournalContainer = document.getElementById('clearJournalContainer');
    clearAllJournalButton = document.getElementById('clearAllJournalButton');
    addManualEntryButton = document.getElementById('addManualEntryButton');
    
    narrowScanModal = document.getElementById('narrowScanModal');
    closeNarrowScanModalButton = document.getElementById('closeNarrowScanModalButton');
    narrowScanInput = document.getElementById('narrowScanInput');
    confirmNarrowScanButton = document.getElementById('confirmNarrowScanButton');

    manualEntryModal = document.getElementById('manualEntryModal');
    manualEntryForm = document.getElementById('manualEntryForm'); // The <form> element itself
    manualTitleInput = document.getElementById('manualTitle');
    manualStatusSelect = document.getElementById('manualStatus');
    manualSummaryTextarea = document.getElementById('manualSummary');
    manualDateInput = document.getElementById('manualDate');
    cancelManualEntryButton = document.getElementById('cancelManualEntryButton');
    // saveManualEntryButton is inside the form, will be handled by form submit
    closeManualEntryModalButton = document.getElementById('closeManualEntryModalButton');

    diaryLoadingOverlay = document.getElementById('diaryLoadingOverlay');
    diaryLoadingIconContainer = document.getElementById('diaryLoadingIconContainer');

    // Initialize icons (since injectSvgs is removed)
    // This is now handled by Python functions directly in the FastHTML components

    // Initial chat message
    chatMessages = [{
        id: Date.now(),
        text: "Hello! I'm Akasi.ai, your virtual health assistant. How are you feeling today? Describe any symptoms you have.",
        sender: 'bot'
    }];
    renderMessages();
    renderStagedAttachments(); // Initialize to hidden
    renderJournalEntries();    // Initialize journal
    startScanAnimation(); 
    updateScannerVisuals(); 
    autoResizeTextarea(chatInput); 

    // Add event listeners (ensure all elements are assigned before this)
    // Example: sendButton.addEventListener('click', handleSendMessage);
    // ... (all other event listeners from your HTML's script tag)
    // For brevity, not re-listing all event listeners here, but they need to be included
    // and adapted to use the globally defined element variables.
}

// Ensure initializeApp is called after DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}