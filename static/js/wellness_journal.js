// --- UTILITY FUNCTIONS ---
function showToast(message, type = 'info') {
  const toastContainer = document.getElementById('toastContainer');
  if (!toastContainer) {
    console.warn("Toast container not found!");
    return;
  }
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

// --- GLOBAL STATE (Client-side only for UI elements not directly managed by HTMX message flow) ---
let stagedAttachments = []; // Still manage staged attachments client-side for preview
let journalIssues = [];     // Journal issues still client-side for this version
let isGeneratingDiaryLoading = false;

const bodyParts = [ // This data could also be fetched or passed from server if it becomes dynamic
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

// --- DOM Elements (Cached on init) ---
let chatInput, fileInput, stagedAttachmentsContainer, messagesEndRef,
    attachImageButton, attachDocumentButton, finishJournalButton,
    journalEntriesList, noJournalEntriesDiv, clearJournalContainer,
    clearAllJournalButton, addManualEntryButton, manualEntryModal,
    manualEntryForm, manualTitleInput, manualStatusSelect,
    manualSummaryTextarea, manualDateInput, cancelManualEntryButton,
    closeManualEntryModalButtonFromDialog, diaryLoadingOverlay; // Renamed one close button ID

function initializeDOMElements() {
    chatInput = document.getElementById('chatInput');
    fileInput = document.getElementById('fileInput');
    stagedAttachmentsContainer = document.getElementById('stagedAttachmentsContainer');
    messagesEndRef = document.getElementById('messagesEndRef'); // Still useful for scrolling
    attachImageButton = document.getElementById('attachImageButton');
    attachDocumentButton = document.getElementById('attachDocumentButton');
    finishJournalButton = document.getElementById('finishJournalButton');
    journalEntriesList = document.getElementById('journalEntriesList');
    noJournalEntriesDiv = document.getElementById('noJournalEntries');
    clearJournalContainer = document.getElementById('clearJournalContainer');
    clearAllJournalButton = document.getElementById('clearAllJournalButton');
    addManualEntryButton = document.getElementById('addManualEntryButton');
    manualEntryModal = document.getElementById('manualEntryModal');
    manualEntryForm = document.getElementById('manualEntryForm');
    manualTitleInput = document.getElementById('manualTitle');
    manualStatusSelect = document.getElementById('manualStatus');
    manualSummaryTextarea = document.getElementById('manualSummary');
    manualDateInput = document.getElementById('manualDate');
    cancelManualEntryButton = document.getElementById('cancelManualEntryButton');
    // Get the specific close button for the manual entry modal from within its structure
    const manualEntryModalDialog = document.getElementById('manualEntryModal');
    if (manualEntryModalDialog) {
        // The close button generated by FastHTML for the dialog form
        closeManualEntryModalButtonFromDialog = manualEntryModalDialog.querySelector('form[method="dialog"] button.btn-ghost');
    }
    diaryLoadingOverlay = document.getElementById('diaryLoadingOverlay');
}

// --- CHATBOX RELATED JS (Now much simpler) ---
function autoResizeTextarea(textarea) {
  if (!textarea) return;
  textarea.style.height = 'auto';
  textarea.style.height = `${Math.max(textarea.scrollHeight, parseInt(getComputedStyle(textarea).minHeight, 10) || 44)}px`;
}

function setupChatInputListeners() {
    if (chatInput) {
        chatInput.addEventListener('input', () => autoResizeTextarea(chatInput));
        // Enter key for submission is now handled by the form submit, HTMX takes over.
        // The hx_on_htmx_after_request on the form will clear and resize.
    }
    // Send button is type="submit", HTMX handles it.
}

// --- Attachment Preview Logic (Remains Client-Side) ---
function setupAttachmentListeners() {
    if (fileInput) {
        fileInput.addEventListener('change', (event) => {
            const files = Array.from(event.target.files);
            if (files.length === 0) return;
            const newStagedFiles = files.map(file => ({
                id: Date.now() + Math.random() + file.name,
                type: file.type.startsWith('image/') ? 'image' : 'document',
                name: file.name,
                url: file.type.startsWith('image/') ? URL.createObjectURL(file) : null, // Use ObjectURL for local preview
                size: `${(file.size / 1024).toFixed(1)} KB`,
                fileObject: file
            }));
            stagedAttachments.push(...newStagedFiles);
            renderStagedAttachments();
            event.target.value = null;
        });
    }
    if (attachImageButton) {
        attachImageButton.addEventListener('click', () => {
            if (!fileInput) return;
            fileInput.accept = 'image/*';
            fileInput.click();
            if (document.activeElement && document.activeElement instanceof HTMLElement && document.activeElement.closest('.dropdown')) {
                document.activeElement.blur();
            }
        });
    }
    if (attachDocumentButton) {
        attachDocumentButton.addEventListener('click', () => {
            if (!fileInput) return;
            fileInput.accept = '.pdf,.doc,.docx,.txt';
            fileInput.click();
            if (document.activeElement && document.activeElement instanceof HTMLElement && document.activeElement.closest('.dropdown')) {
                document.activeElement.blur();
            }
        });
    }
}

function renderStagedAttachments() {
  if (!stagedAttachmentsContainer) return;
  if (stagedAttachments.length > 0) {
    stagedAttachmentsContainer.classList.remove('hidden');
    stagedAttachmentsContainer.innerHTML = '';
    stagedAttachments.forEach(attachment => {
      const attachmentDiv = document.createElement('div');
      attachmentDiv.className = 'p-1.5 border border-base-300 rounded bg-base-100 relative flex items-center gap-2';
      let iconHTML = attachment.type === 'image' && attachment.url ?
        `<img src="${attachment.url}" alt="Staged" class="h-10 w-10 object-cover rounded border border-base-300"/>` :
        `<span class="emoji-icon text-2xl text-primary flex-shrink-0">📄</span>`;

      attachmentDiv.innerHTML = `
        ${iconHTML}
        <div class="flex-grow overflow-hidden">
          <p class="text-xs font-medium text-base-content/90 truncate">${attachment.name}</p>
          <p class="text-xs text-base-content/70">${attachment.type === 'image' ? 'Image' : 'Document'} (${attachment.size})</p>
        </div>
        <button class="btn btn-xs btn-circle btn-ghost text-error" data-id="${attachment.id}" title="Remove attachment">
          <span class="emoji-icon">❌</span>
        </button>`;
      attachmentDiv.querySelector('button').addEventListener('click', () => removeStagedAttachment(attachment.id));
      stagedAttachmentsContainer.appendChild(attachmentDiv);
    });
  } else {
    stagedAttachmentsContainer.classList.add('hidden');
    stagedAttachmentsContainer.innerHTML = '';
  }
}

function removeStagedAttachment(fileIdToRemove) {
  const attachmentToRemove = stagedAttachments.find(file => file.id === fileIdToRemove);
  if (attachmentToRemove && attachmentToRemove.type === 'image' && attachmentToRemove.url && attachmentToRemove.url.startsWith('blob:')) {
    URL.revokeObjectURL(attachmentToRemove.url); // Revoke object URL to free memory
  }
  stagedAttachments = stagedAttachments.filter(file => file.id !== fileIdToRemove);
  renderStagedAttachments();
}

// Chat header buttons (Add AI, Add User, Clear Chat) are now HTMX driven.
// No specific JS needed for their core action, only for UI side-effects if any.

// --- AUTOMATED JOURNAL ENTRY FROM CHAT (Client-side based on chat input for now) ---
// This logic might eventually move server-side if chat processing becomes more complex
function addAutomatedJournalEntry(matchedPart) {
    if (!matchedPart) return;
    const severity = Math.floor(Math.random() * 3) + 1;
    const newIssueEntry = {
        id: Date.now(),
        partName: matchedPart.label,
        description: matchedPart.description,
        severity,
        timestamp: new Date().toLocaleString()
    };
    journalIssues = [newIssueEntry, ...journalIssues].slice(0, 10);
    renderJournalEntries();
}

function handleSymptomInputForJournal(text) { // Changed to accept text directly
    if (isGeneratingDiaryLoading) return;
    if (text && text.trim() !== '') {
        const lowerInput = text.toLowerCase();
        let matchedPart = null;
        for (const part of bodyParts) {
            if (part.keywords.some(keyword => lowerInput.includes(keyword))) {
                matchedPart = part;
                break;
            }
        }
        if (matchedPart) {
            addAutomatedJournalEntry(matchedPart);
        }
    }
}

// Listen for HTMX afterSettle event to process chat text for journal entries
// This ensures we process the text after HTMX has updated the DOM with the new message
document.body.addEventListener('htmx:afterSettle', function(event) {
    // Check if the event target is the messagesArea or a child of it
    const messagesArea = document.getElementById('messagesArea');
    if (messagesArea && (event.target === messagesArea || messagesArea.contains(event.target))) {
        // Find the last user message text. This is a bit simplistic and might need refinement.
        // It assumes the last added elements are the user and bot messages.
        const userMessages = messagesArea.querySelectorAll('.chat-bubble-primary .chat-message-text');
        if (userMessages.length > 0) {
            const lastUserMessageText = userMessages[userMessages.length - 1].textContent;
            handleSymptomInputForJournal(lastUserMessageText);
        }
        // Ensure scroll to bottom after HTMX adds content
        const messagesEndRef = document.getElementById('messagesEndRef');
        if(messagesEndRef) messagesEndRef.scrollIntoView({behavior: "smooth"});
    }
});


// --- JOURNAL PANEL LOGIC (Remains Client-Side) ---
function getSeverityClassAndText(severity) {
  switch (severity) {
    case 3: return { classes: 'text-red-700 border-red-400 bg-red-100', text: 'High' };
    case 2: return { classes: 'text-yellow-700 border-yellow-400 bg-yellow-100', text: 'Medium' };
    case 1: return { classes: 'text-green-700 border-green-400 bg-green-100', text: 'Low' };
    default: return { classes: 'text-gray-600 border-gray-300 bg-gray-100', text: 'N/A' };
  }
}

function renderJournalEntries() {
  if (!journalEntriesList || !noJournalEntriesDiv || !clearJournalContainer) return;
  journalEntriesList.innerHTML = '';
  if (journalIssues.length === 0) {
    noJournalEntriesDiv.style.display = 'flex';
    clearJournalContainer.style.display = 'none';
  } else {
    noJournalEntriesDiv.style.display = 'none';
    clearJournalContainer.style.display = 'flex';
    journalIssues.forEach(issue => {
      const severityInfo = getSeverityClassAndText(issue.severity);
      const entryDiv = document.createElement('div');
      entryDiv.className = 'bg-base-100/80 backdrop-blur-sm rounded-lg p-3 shadow-md hover:shadow-lg transition-shadow border border-base-300/80 animate-slideUp';
      entryDiv.innerHTML = `
        <div class="flex justify-between items-start mb-1">
          <h3 class="font-medium text-base-content/90 text-sm">${issue.partName}</h3>
          <span class="text-xs font-semibold px-2 py-0.5 rounded-full border ${severityInfo.classes}">
            ${severityInfo.text}
          </span>
        </div>
        <p class="text-base-content/80 text-xs mb-1.5 leading-relaxed">${issue.description.split('.')[0]}.</p>
        <p class="text-base-content/70 text-xs text-right">${new Date(issue.timestamp).toLocaleDateString()}</p>`;
      journalEntriesList.appendChild(entryDiv);
    });
  }
  journalEntriesList.scrollTop = 0;
}

function setupManualEntryModal() {
    if (addManualEntryButton) {
        addManualEntryButton.addEventListener('click', () => {
            if (isGeneratingDiaryLoading) return;
            if (manualEntryForm) manualEntryForm.reset();
            if (manualDateInput) manualDateInput.value = new Date().toISOString().split('T')[0];
            if (manualEntryModal) manualEntryModal.showModal();
        });
    }
    if (cancelManualEntryButton && manualEntryModal) {
        cancelManualEntryButton.addEventListener('click', () => manualEntryModal.close());
    }
    // The DaisyUI modal close button (X) inside the form[method="dialog"]
    if (closeManualEntryModalButtonFromDialog && manualEntryModal) {
        closeManualEntryModalButtonFromDialog.addEventListener('click', () => manualEntryModal.close());
    }
    if (manualEntryForm) {
        manualEntryForm.addEventListener('submit', (e) => {
            e.preventDefault();
            if (!manualTitleInput || !manualSummaryTextarea || !manualStatusSelect || !manualDateInput) return;
            const title = manualTitleInput.value.trim();
            const summary = manualSummaryTextarea.value.trim();
            if (!title || !summary) {
                showToast("Title and Summary are required for manual entry.", "warning"); return;
            }
            const newManualIssue = {
                id: Date.now(), partName: title, description: summary,
                severity: parseInt(manualStatusSelect.value, 10),
                timestamp: new Date(manualDateInput.value + "T00:00:00").toLocaleString()
            };
            journalIssues = [newManualIssue, ...journalIssues].slice(0, 10);
            renderJournalEntries();
            if (manualEntryModal) manualEntryModal.close();
        });
    }
}

function setupJournalControls() {
    if (clearAllJournalButton) {
        clearAllJournalButton.addEventListener('click', () => {
            if (isGeneratingDiaryLoading) return;
            journalIssues = []; renderJournalEntries();
        });
    }
    if (finishJournalButton) {
        finishJournalButton.addEventListener('click', () => {
            if (journalIssues.length === 0) {
                if (!confirm("Your current session journal is empty. Proceed anyway?")) return;
            }
            isGeneratingDiaryLoading = true;
            if (diaryLoadingOverlay) diaryLoadingOverlay.style.display = 'flex';
            const buttonsToDisable = [
                finishJournalButton, addManualEntryButton, clearAllJournalButton,
                ...document.querySelectorAll('#chatboxHeader button'), // HTMX buttons are not disabled by JS
                document.getElementById('attachmentButton'), // Attachment button itself
                // Scanner buttons
                document.getElementById('debugStartScanButton'), document.getElementById('debugStopScanButton'),
                document.getElementById('debugNarrowScanButton'), document.getElementById('debugFullBodyGlowButton'),
                document.getElementById('restartScanButton')
            ];
            // Disable chat input form elements
            const chatForm = document.getElementById('chatInputForm');
            if(chatForm) Array.from(chatForm.elements).forEach(el => el.disabled = true);

            buttonsToDisable.forEach(btn => { if(btn) btn.disabled = true; });

            setTimeout(() => {
                showToast("Wellness Journal compilation simulated: " + (journalIssues.length > 0 ? journalIssues.map(i => i.partName).join(', ') : "No issues logged."), "info");
                isGeneratingDiaryLoading = false;
                if (diaryLoadingOverlay) diaryLoadingOverlay.style.display = 'none';
                buttonsToDisable.forEach(btn => { if(btn) btn.disabled = false; });
                if(chatForm) Array.from(chatForm.elements).forEach(el => el.disabled = false);
            }, 2500);
        });
    }
}

// --- SCANNER UI (Placeholder Logic) ---
function setupScannerPlaceholders() {
    const scannerStatusTextEl = document.getElementById('scannerStatusText');
    if (scannerStatusTextEl) {
        scannerStatusTextEl.textContent = 'Scanner ready. Describe symptoms or start a scan.';
    }
    const debugStartScanButton = document.getElementById('debugStartScanButton');
    if (debugStartScanButton) {
        debugStartScanButton.addEventListener('click', () => {
            if (scannerStatusTextEl) scannerStatusTextEl.textContent = 'Simulating scan start...';
            showToast('Debug: Scan Started (simulation)', 'info');
        });
    }
    const debugStopScanButton = document.getElementById('debugStopScanButton');
     if (debugStopScanButton) {
        debugStopScanButton.addEventListener('click', () => {
            if (scannerStatusTextEl) scannerStatusTextEl.textContent = 'Simulating scan stop...';
            showToast('Debug: Scan Stopped (simulation)', 'info');
        });
    }
}

// --- INITIALIZATION ---
function initializeApp() {
  initializeDOMElements();

  // Initial chat messages are now rendered by the server.
  // Client-side chatMessages array is no longer the source of truth for rendering.

  renderStagedAttachments(); // For any attachments potentially staged on a page reload (though unlikely here)
  renderJournalEntries();    // Render initial empty state or any client-side persisted journal entries
  if (chatInput) autoResizeTextarea(chatInput);

  setupChatInputListeners();   // For textarea resize
  setupAttachmentListeners();  // For client-side file preview
  setupManualEntryModal();     // For manual journal entry modal
  setupJournalControls();      // For "Clear All" and "Finish Journal"
  setupScannerPlaceholders();  // For basic scanner UI feedback

  // Dropdown closing logic (if not fully handled by DaisyUI + HTMX focus)
  document.addEventListener('click', function(event) {
    const attachmentDropdownContainer = document.getElementById('attachmentOptionsDropdownContainer');
    if (attachmentDropdownContainer && !attachmentDropdownContainer.contains(event.target) && !attachmentDropdownContainer.querySelector('button').contains(event.target)) {
        const attachmentOptionsContent = document.getElementById('attachmentOptionsContent');
        // DaisyUI dropdowns close on blur. If an item was clicked, it might have already blurred.
        // This is a fallback.
        if (attachmentOptionsContent && attachmentOptionsContent.classList.contains('menu')) { // Check if it's a DaisyUI menu that might be open
             if (document.activeElement && document.activeElement instanceof HTMLElement && document.activeElement.closest('.dropdown')) {
                 document.activeElement.blur();
            }
        }
    }
  });

  // Initial scroll to bottom for chat (server now renders messages, but good to ensure)
  setTimeout(() => {
    if(messagesEndRef) messagesEndRef.scrollIntoView({behavior: "auto"});
  },100);

}

document.addEventListener('DOMContentLoaded', initializeApp);
