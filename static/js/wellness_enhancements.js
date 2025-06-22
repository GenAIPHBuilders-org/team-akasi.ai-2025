const SCAN_START_Y_VIEWBOX = 32;
const SCAN_END_Y_VIEWBOX = 165;
const SCAN_SPEED_UNITS_PER_INTERVAL = 1.0;

let globalScanLinePosition = SCAN_START_Y_VIEWBOX;
let globalScanLineDirection = 'down';
let globalIsLineScanning = false;
let globalScanLineAnimationInterval = null;

let globalIsFtBodyOutlinePulsating = false;

let globalNarrowScannedPartEl = null;

let scanLineAnimationGroupRawEl = null;
let scanLineAnimationElementRawEl = null;
let scanLineHighlightAnimationElementRawEl = null;
let mainAnatomySvgFtEl = null;
let generalScannerStatusTextEl = null;
let generalScannerStatusIconContainerEl = null;
let narrowScanModalEl = null;
let narrowScanInputEl = null;
let confirmNarrowScanButtonEl = null;
let closeNarrowScanModalButtonEl = null;

let stagedFilesData = [];

let fileInputEl = null;
let stagedAttachmentsContainerEl = null;
let chatFormEl = null;
let chatInputEl = null;

let manualEntryModalJsEl = null;
let manualEntryFormJsEl = null;
let manualDateInputJsEl = null;
let addManualEntryButtonJsEl = null;
let cancelManualEntryButtonJsEl = null;
let closeManualEntryModalButtonJsEl = null;

// New elements for personal-info style interactions
let chatHistoryButton = null;
let chatHistoryOverlay = null;
let closeChatHistory = null;
let chatMessages = null;
let bodyScannerButton = null;
let bodyScannerOverlay = null;
let closeBodScanner = null;

// Chat history state
let conversationHistory = [];

// ========================================
// CHAT HISTORY FUNCTIONALITY (from personal-info)
// ========================================

function initializeChatHistoryElements() {
    chatHistoryButton = document.getElementById('chat-history-button');
    chatHistoryOverlay = document.getElementById('chat-history-overlay');
    closeChatHistory = document.getElementById('close-chat-history');
    chatMessages = document.getElementById('chat-messages');
    bodyScannerButton = document.getElementById('body-scanner-button');
    bodyScannerOverlay = document.getElementById('body-scanner-overlay');
    closeBodScanner = document.getElementById('close-body-scanner');

    // Setup chat history interactions
    if (chatHistoryButton) {
        chatHistoryButton.addEventListener('click', showChatHistory);
    }

    if (closeChatHistory) {
        closeChatHistory.addEventListener('click', hideChatHistory);
    }

    if (chatHistoryOverlay) {
        chatHistoryOverlay.addEventListener('click', (e) => {
            if (e.target === chatHistoryOverlay) {
                hideChatHistory();
            }
        });
    }

    // Setup body scanner modal interactions
    if (bodyScannerButton) {
        bodyScannerButton.addEventListener('click', showBodyScannerModal);
    }

    if (closeBodScanner) {
        closeBodScanner.addEventListener('click', hideBodyScannerModal);
    }

    if (bodyScannerOverlay) {
        bodyScannerOverlay.addEventListener('click', (e) => {
            if (e.target === bodyScannerOverlay) {
                hideBodyScannerModal();
            }
        });
    }

    console.log("Chat history and body scanner elements initialized");
}

function initializeChatHistory() {
    // Initialize with Akasi's welcome message
    const initialMessage = "Hi there! I'm Akasi, your personal wellness assistant. I help you track your health by building a wellness journal. I've activated my body scanner to check how you're doing. Just start by telling me how you feel today. You can also add notes, symptoms, photos, or any medical documents along the way. Let's begin!";
    addMessageToHistory('akasi', initialMessage);
}

function addMessageToHistory(type, message) {
    const timestamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
    const messageEntry = {
        type: type, // 'akasi' or 'user'
        message: message,
        timestamp: timestamp
    };
    
    conversationHistory.push(messageEntry);
    
    // Save to localStorage
    localStorage.setItem('wellness_chat_history', JSON.stringify(conversationHistory));
    
    // Update chat history modal in real-time if it's currently open
    updateChatHistoryIfOpen();
}

function renderChatHistory() {
    if (!chatMessages) return;

    // Load chat history from localStorage if available
    const storedHistory = localStorage.getItem('wellness_chat_history');
    if (storedHistory) {
        conversationHistory = JSON.parse(storedHistory);
    }

    if (conversationHistory.length === 0) {
        chatMessages.innerHTML = `
            <div style="text-align: center; color: rgba(255, 255, 255, 0.7); padding: 2rem; font-style: italic;">
                No conversation history yet. Start chatting to see your messages here!
            </div>
        `;
        return;
    }

    const messagesHTML = conversationHistory.map(entry => {
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

    chatMessages.innerHTML = messagesHTML;
}

function showChatHistory() {
    if (chatHistoryOverlay) {
        // Render the chat history
        renderChatHistory();
        
        // Show the overlay with animation
        chatHistoryOverlay.style.display = 'block';
        // Force a reflow to ensure the display change takes effect
        chatHistoryOverlay.offsetHeight;
        // Add the show class for animation
        chatHistoryOverlay.classList.add('show');
        
        // Scroll to bottom after a short delay to allow messages to load
        setTimeout(() => {
            if (chatMessages) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }, 100);
    }
}

function hideChatHistory() {
    if (chatHistoryOverlay) {
        // Remove show class for animation
        chatHistoryOverlay.classList.remove('show');
        
        // Hide after animation completes
        setTimeout(() => {
            chatHistoryOverlay.style.display = 'none';
        }, 300);
    }
}

function updateChatHistoryIfOpen() {
    // Check if chat history modal is currently visible/open
    if (chatHistoryOverlay && 
        chatHistoryOverlay.style.display === 'block' && 
        chatHistoryOverlay.classList.contains('show')) {
        
        // Re-render the chat history to include the new message
        renderChatHistory();
        
        // Auto-scroll to bottom to show the latest message
        setTimeout(() => {
            if (chatMessages) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }, 50); // Small delay to ensure DOM update
    }
}

// ========================================
// BODY SCANNER MODAL FUNCTIONALITY
// ========================================

function showBodyScannerModal() {
    if (bodyScannerOverlay) {
        bodyScannerOverlay.style.display = 'block';
        // Force a reflow to ensure the display change takes effect
        bodyScannerOverlay.offsetHeight;
        // Add the show class for animation
        bodyScannerOverlay.classList.add('show');
        
        // Start the body scanner animation automatically when modal opens
        setTimeout(() => {
            startBodyScanAnimation();
        }, 500);
    }
}

function hideBodyScannerModal() {
    if (bodyScannerOverlay) {
        // Remove show class for animation
        bodyScannerOverlay.classList.remove('show');
        
        // Hide after animation completes
        setTimeout(() => {
            bodyScannerOverlay.style.display = 'none';
            // Stop scanner animation when modal closes
            stopBodyScanAnimation();
        }, 300);
    }
}

// ========================================
// ENHANCED CHAT MONITORING
// ========================================

function initializeChatMessageMonitoring() {
    // Monitor for new chat messages via HTMX afterSwap events
    document.body.addEventListener('htmx:afterSwap', function(event) {
        const messagesArea = document.getElementById('messagesArea');
        if (messagesArea && (event.target === messagesArea || (messagesArea.contains && messagesArea.contains(event.target)))) {
            // Extract the latest messages for chat history
            extractAndSaveNewMessages();
        }
    });

    // Monitor form submissions to capture user messages
    if (chatFormEl) {
        chatFormEl.addEventListener('htmx:beforeRequest', function(event) {
            const formData = new FormData(chatFormEl);
            const userMessage = formData.get('chatInput');
            if (userMessage && userMessage.trim()) {
                addMessageToHistory('user', userMessage.trim());
            }
        });

        chatFormEl.addEventListener('htmx:afterRequest', function(event) {
            if (event.detail.successful) {
                // Wait a bit for HTMX to process, then extract AI response
                setTimeout(() => {
                    extractLatestAIMessage();
                }, 500);
            }
        });
    }
}

function extractAndSaveNewMessages() {
    // This function attempts to extract messages from the hidden messagesArea
    // and save them to chat history
    const messagesArea = document.getElementById('messagesArea');
    if (!messagesArea) return;

    const allMessages = messagesArea.querySelectorAll('.chat-message-container');
    if (allMessages.length === 0) return;

    // Get the last message and determine if it's from AI
    const lastMessage = allMessages[allMessages.length - 1];
    const messageText = lastMessage.querySelector('.chat-message-text');
    
    if (messageText && lastMessage.querySelector('.avatar.placeholder.bg-base-300')) {
        // This is an AI message
        const aiText = messageText.textContent.trim();
        if (aiText && !isMessageAlreadyInHistory(aiText)) {
            addMessageToHistory('akasi', aiText);
        }
    }
}

function extractLatestAIMessage() {
    // Alternative method to extract AI messages
    const messagesArea = document.getElementById('messagesArea');
    if (!messagesArea) return;

    const aiMessages = messagesArea.querySelectorAll('.chat-bubble-neutral .chat-message-text');
    if (aiMessages.length > 0) {
        const lastAIMessage = aiMessages[aiMessages.length - 1];
        const aiText = lastAIMessage.textContent.trim();
        if (aiText && !isMessageAlreadyInHistory(aiText)) {
            addMessageToHistory('akasi', aiText);
        }
    }
}

function isMessageAlreadyInHistory(messageText) {
    return conversationHistory.some(entry => entry.message === messageText);
}

function initializeChatAttachmentElements() {
    fileInputEl = document.getElementById('fileInput');
    stagedAttachmentsContainerEl = document.getElementById('stagedAttachmentsContainer');
    chatFormEl = document.getElementById('chatForm');
    chatInputEl = document.getElementById('chatInput');

    // File input already has onclick handler in HTML, so just add change listener
    if (fileInputEl) {
        fileInputEl.addEventListener('change', handleFileSelection);
    }

    if (chatFormEl) {
        // IMPORTANT: Override HTMX's FormData construction
        chatFormEl.addEventListener('htmx:configRequest', function(event) {
            const formData = new FormData();

            // Get the chatInput element directly from the form that triggered the event
            const currentChatInputElement = event.target.elements.chatInput;

            if (currentChatInputElement) {
                formData.append('chatInput', currentChatInputElement.value);
            } else {
                console.warn("chatInput element not found by name in the form during htmx:configRequest. Trying by ID from global scope as fallback.");
                const currentChatInputById = document.getElementById('chatInput');
                if (currentChatInputById) {
                     formData.append('chatInput', currentChatInputById.value);
                } else if (chatInputEl) {
                    formData.append('chatInput', chatInputEl.value);
                    console.warn("Fell back to globally scoped chatInputEl. This might send stale data if OOB swaps occurred.");
                } else {
                    console.error("Completely unable to find chatInput to append to FormData.");
                }
            }

            // Append staged files
            let hasFiles = false;
            stagedFilesData.forEach(stagedFile => {
                formData.append('files', stagedFile.file, stagedFile.file.name);
                hasFiles = true;
            });

            event.detail.parameters = formData;

            if (hasFiles) {
                // Let the browser set the Content-Type for FormData (multipart/form-data with boundary)
                delete event.detail.headers['Content-Type'];
            }
        });

        // Clear staged files and input after successful HTMX request
        chatFormEl.addEventListener('htmx:afterRequest', function(event) {
            if (event.detail.successful) {
                clearStagedFilesAndInput();
            }
        });
    }
}

function handleFileSelection(event) {
    const files = event.target.files;
    if (!files) return;
    const maxFiles = 5;
    const maxSizePerFile = 5 * 1024 * 1024;

    if (stagedFilesData.length + files.length > maxFiles) {
        showToast(`You can attach a maximum of ${maxFiles} files.`, 'warning');
        event.target.value = null;
        return;
    }

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        if (stagedFilesData.some(sf => sf.file.name === file.name && sf.file.size === file.size)) {
            showToast(`File "${file.name}" is already staged.`, 'info');
            continue;
        }
        if (file.size > maxSizePerFile) {
            showToast(`File "${file.name}" is too large (max ${maxSizePerFile / (1024 * 1024)}MB).`, 'warning');
            continue;
        }
        const fileId = `staged-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
        const displayType = file.type.startsWith('image/') ? 'image' : 'document';
        stagedFilesData.push({ id: fileId, file: file, type: displayType });
    }
    renderStagedAttachments();
    event.target.value = null;
}

function renderStagedAttachments() {
    if (!stagedAttachmentsContainerEl) return;
    stagedAttachmentsContainerEl.innerHTML = '';

    if (stagedFilesData.length === 0) {
        stagedAttachmentsContainerEl.classList.add('hidden');
        return;
    }
    stagedAttachmentsContainerEl.classList.remove('hidden');

    stagedFilesData.forEach(stagedFile => {
        const attachmentEl = document.createElement('div');
        attachmentEl.className = 'staged-attachment-item flex items-center justify-between p-1.5 bg-white/10 rounded text-xs mb-1 group';
        attachmentEl.dataset.fileId = stagedFile.id;

        const fileInfo = document.createElement('div');
        fileInfo.className = 'flex items-center overflow-hidden mr-2 flex-grow';

        const icon = document.createElement('span');
        icon.className = 'material-icons text-lg mr-1.5 text-white/80 flex-shrink-0';
        
        if (stagedFile.type === 'image') {
            icon.textContent = 'image';
        } else if (stagedFile.file.name.toLowerCase().endsWith('.pdf')) {
            icon.textContent = 'picture_as_pdf';
        } else if (stagedFile.file.name.toLowerCase().match(/\.(doc|docx)$/)) {
            icon.textContent = 'description';
        } else {
            icon.textContent = 'article';
        }

        const nameAndSizeDiv = document.createElement('div');
        nameAndSizeDiv.className = 'flex flex-col overflow-hidden';

        const name = document.createElement('span');
        name.className = 'truncate text-white/90 text-xs';
        name.textContent = stagedFile.file.name;
        name.title = stagedFile.file.name;

        const size = document.createElement('span');
        size.className = 'text-white/70 text-xs';
        size.textContent = `${(stagedFile.file.size / 1024).toFixed(1)} KB`;

        nameAndSizeDiv.appendChild(name);
        nameAndSizeDiv.appendChild(size);

        fileInfo.appendChild(icon);
        fileInfo.appendChild(nameAndSizeDiv);

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'text-white/50 hover:text-red-400 transition-colors flex-shrink-0 p-1';
        removeBtn.innerHTML = '<span class="material-icons text-base">close</span>';
        removeBtn.title = 'Remove attachment';
        removeBtn.onclick = (e) => {
            e.stopPropagation();
            removeStagedFile(stagedFile.id);
        };

        attachmentEl.appendChild(fileInfo);
        attachmentEl.appendChild(removeBtn);
        stagedAttachmentsContainerEl.appendChild(attachmentEl);
    });
}

function removeStagedFile(fileIdToRemove) {
    stagedFilesData = stagedFilesData.filter(sf => sf.id !== fileIdToRemove);
    renderStagedAttachments();
}

function clearStagedFilesAndInput() {
    stagedFilesData = [];
    if (fileInputEl) {
        fileInputEl.value = null;
    }
    if (stagedAttachmentsContainerEl) {
        renderStagedAttachments();
    }
}

function initializeScanAnimationElements() {
    scanLineAnimationGroupRawEl = document.getElementById('scanLineAnimationGroupRaw');
    scanLineAnimationElementRawEl = document.getElementById('scanLineAnimationElementRaw');
    scanLineHighlightAnimationElementRawEl = document.getElementById('scanLineHighlightAnimationElementRaw');

    generalScannerStatusTextEl = document.getElementById('scannerStatusText');
    generalScannerStatusIconContainerEl = document.getElementById('scannerStatusIconContainer');

    mainAnatomySvgFtEl = document.getElementById('mainAnatomySvgFT');

    narrowScanModalEl = document.getElementById('narrowScanModal');
    narrowScanInputEl = document.getElementById('narrowScanInput');
    confirmNarrowScanButtonEl = document.getElementById('confirmNarrowScanButton');
    closeNarrowScanModalButtonEl = document.getElementById('closeNarrowScanModalButton');

    // Bind narrow scan button in the body scanner modal
    const narrowScanButton = document.getElementById('narrowScanButton');
    if (narrowScanButton && narrowScanModalEl) {
        narrowScanButton.addEventListener('click', () => {
            if (typeof narrowScanModalEl.showModal === 'function') {
                narrowScanModalEl.showModal();
            }
        });
    }

    console.log("Scan animation elements initialized:",
        !!scanLineAnimationGroupRawEl,
        !!generalScannerStatusTextEl,
        !!mainAnatomySvgFtEl,
        !!narrowScanModalEl
    );

    if (confirmNarrowScanButtonEl && narrowScanModalEl && narrowScanInputEl) {
        confirmNarrowScanButtonEl.addEventListener('click', handleConfirmManualNarrowScan);
    }
    if (closeNarrowScanModalButtonEl && narrowScanModalEl) {
        closeNarrowScanModalButtonEl.addEventListener('click', () => {
            if (narrowScanModalEl && typeof narrowScanModalEl.close === 'function') {
                narrowScanModalEl.close();
            }
        });
    }
    if (narrowScanModalEl) {
        narrowScanModalEl.addEventListener('close', () => {
            if(narrowScanInputEl) narrowScanInputEl.value = '';
        });
    }

    updateScanAnimationVisuals();
}

function updateScanAnimationVisuals() {
    if (!generalScannerStatusTextEl || !generalScannerStatusIconContainerEl || !mainAnatomySvgFtEl) {
        console.error("Scanner visual elements not fully initialized for updateScanAnimationVisuals.");
        return;
    }

    let iconEmoji = '❓';
    generalScannerStatusIconContainerEl.classList.remove('animate-pulse', 'animate-subtle-spin');

    if (globalNarrowScannedPartEl && globalNarrowScannedPartEl.classList.contains('ft-narrow-scan-blue-pulsate')) {
        if (scanLineAnimationGroupRawEl) scanLineAnimationGroupRawEl.style.display = 'none';
        if (mainAnatomySvgFtEl.classList.contains('ft-body-outline-pulsating')) {
             mainAnatomySvgFtEl.classList.remove('ft-body-outline-pulsating');
             globalIsFtBodyOutlinePulsating = false;
        }
        generalScannerStatusTextEl.textContent = `Narrow scan: ${globalNarrowScannedPartEl.dataset.name || 'Selected Part'}`;
        iconEmoji = '🎯';
        generalScannerStatusIconContainerEl.classList.add('animate-pulse');
    }
    else if (globalIsFtBodyOutlinePulsating) {
        if (scanLineAnimationGroupRawEl) scanLineAnimationGroupRawEl.style.display = 'none';
        generalScannerStatusTextEl.textContent = "Full body outline pulsating...";
        iconEmoji = '💡';
        generalScannerStatusIconContainerEl.classList.add('animate-pulse');
    }
    else if (globalIsLineScanning) {
        if (scanLineAnimationGroupRawEl && scanLineAnimationElementRawEl && scanLineHighlightAnimationElementRawEl) {
            scanLineAnimationGroupRawEl.style.display = 'block';
            scanLineAnimationElementRawEl.setAttribute('y1', String(globalScanLinePosition));
            scanLineAnimationElementRawEl.setAttribute('y2', String(globalScanLinePosition));
            scanLineHighlightAnimationElementRawEl.setAttribute('y', String(globalScanLinePosition - 2.5));
        }
        generalScannerStatusTextEl.textContent = 'Full body scan in progress...';
        iconEmoji = '💓';
    }
    else {
        if (scanLineAnimationGroupRawEl) scanLineAnimationGroupRawEl.style.display = 'none';
        generalScannerStatusTextEl.textContent = 'Scanner idle.';
        iconEmoji = '💤';
    }

    generalScannerStatusIconContainerEl.textContent = iconEmoji;
}

function startScanLineAnimationInterval() {
    if (globalScanLineAnimationInterval) clearInterval(globalScanLineAnimationInterval);

    if (!globalIsLineScanning || globalIsFtBodyOutlinePulsating || globalNarrowScannedPartEl) {
        updateScanAnimationVisuals();
        return;
    }

    globalScanLineAnimationInterval = setInterval(() => {
        if (globalScanLineDirection === 'down') {
            globalScanLinePosition += SCAN_SPEED_UNITS_PER_INTERVAL;
            if (globalScanLinePosition >= SCAN_END_Y_VIEWBOX) {
                globalScanLinePosition = SCAN_END_Y_VIEWBOX;
                globalScanLineDirection = 'up';
            }
        } else {
            globalScanLinePosition -= SCAN_SPEED_UNITS_PER_INTERVAL;
            if (globalScanLinePosition <= SCAN_START_Y_VIEWBOX) {
                globalScanLinePosition = SCAN_START_Y_VIEWBOX;
                globalScanLineDirection = 'down';
            }
        }
        updateScanAnimationVisuals();
    }, 30);
}

function stopScanLineAnimationInterval() {
    if (globalScanLineAnimationInterval) clearInterval(globalScanLineAnimationInterval);
    globalScanLineAnimationInterval = null;
}

function clearAllEffects() {
    if (globalIsFtBodyOutlinePulsating && mainAnatomySvgFtEl) {
        mainAnatomySvgFtEl.classList.remove('ft-body-outline-pulsating');
    }
    globalIsFtBodyOutlinePulsating = false;

    if (globalNarrowScannedPartEl) {
        globalNarrowScannedPartEl.classList.remove('ft-narrow-scan-blue-pulsate');
        globalNarrowScannedPartEl = null;
    }
}

function triggerNarrowScanForPart(partName) {
    console.log(`Attempting narrow scan for: ${partName}`);
    if (!mainAnatomySvgFtEl) {
        console.error("Main anatomy SVG not found for narrow scan.");
        showToast("Error: Body scanner component not ready.", "error");
        return;
    }

    const searchTerm = partName.trim().toLowerCase();
    if (!searchTerm) {
        showToast("Error: No body part specified for narrow scan.", "warning");
        return;
    }

    let foundPart = null;
    const allParts = mainAnatomySvgFtEl.querySelectorAll('.body-part');
    for (const part of allParts) {
        const currentPartName = (part.dataset.name || part.id.replace(/_group/g, '').replace(/_/g, ' ')).toLowerCase();
        if (currentPartName.includes(searchTerm)) {
            foundPart = part;
            break;
        }
    }

    if (foundPart) {
        clearAllEffects();
        globalNarrowScannedPartEl = foundPart;
        globalNarrowScannedPartEl.classList.add('ft-narrow-scan-blue-pulsate');

        globalIsLineScanning = false;
        stopScanLineAnimationInterval();

        updateScanAnimationVisuals();
        showToast(`Narrow scan: ${foundPart.dataset.name || partName}`, "success");
    } else {
        console.warn(`Body part "${partName}" not found for narrow scan.`);
        showToast(`Could not locate part: ${partName}. Try general scan.`, "error");
    }
}

function handleConfirmManualNarrowScan() {
    if (!narrowScanInputEl || !narrowScanModalEl) return;
    const partNameFromInput = narrowScanInputEl.value;
    triggerNarrowScanForPart(partNameFromInput);
    if (typeof narrowScanModalEl.close === 'function') {
        narrowScanModalEl.close();
    }
}

function startBodyScanAnimation() {
    console.log("startBodyScanAnimation called");
    clearAllEffects();

    globalScanLinePosition = SCAN_START_Y_VIEWBOX;
    globalScanLineDirection = 'down';
    globalIsLineScanning = true;

    stopScanLineAnimationInterval();
    startScanLineAnimationInterval();
    updateScanAnimationVisuals();
}

function stopBodyScanAnimation() {
    console.log("stopBodyScanAnimation called");
    globalIsLineScanning = false;
    stopScanLineAnimationInterval();
    updateScanAnimationVisuals();
}

function toggleBodyGlowEffect() {
    console.log("toggleBodyGlowEffect called (for FT SVG outline pulsate)");

    const wasPulsating = globalIsFtBodyOutlinePulsating;
    clearAllEffects();

    globalIsFtBodyOutlinePulsating = !wasPulsating;

    if (globalIsFtBodyOutlinePulsating) {
        globalIsLineScanning = false;
        stopScanLineAnimationInterval();
        if (mainAnatomySvgFtEl) {
            mainAnatomySvgFtEl.classList.add('ft-body-outline-pulsating');
        }
    } else {
        if (mainAnatomySvgFtEl) {
            mainAnatomySvgFtEl.classList.remove('ft-body-outline-pulsating');
        }
    }
    updateScanAnimationVisuals();
}

function executeBodyScannerCommand(command) {
    console.log(`Executing body scanner command: ${command}`);
    if (!command || command.trim() === "" || command.toLowerCase() === "idle") {
        console.log("Scanner command is idle or empty, no action taken.");
        return;
    }

    const upperCommand = command.toUpperCase();

    switch (upperCommand) {
        case "START_SCAN":
            startBodyScanAnimation();
            break;
        case "STOP_SCAN":
            stopBodyScanAnimation();
            break;
        case "FULL_BODY_GLOW":
            toggleBodyGlowEffect();
            break;
        default:
            triggerNarrowScanForPart(command);
            break;
    }
}

if (typeof showToast === 'undefined') {
    function showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            console.error("Toast container not found. Cannot display toast:", message);
            alert(message);
            return;
        }
        const toastId = `toast-js-${Date.now()}`;
        let alertClass = 'alert-info';
        if (type === 'success') alertClass = 'alert-success';
        if (type === 'error') alertClass = 'alert-error';
        if (type === 'warning') alertClass = 'alert-warning';

        const toastHTML = `
            <div id="${toastId}" class="alert ${alertClass} shadow-lg opacity-0 transform translate-y-2 transition-all duration-300 ease-out">
                <span>${message}</span>
            </div>
        `;
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);

        setTimeout(() => {
            const toastElement = document.getElementById(toastId);
            if(toastElement) {
                toastElement.style.opacity = '1';
                toastElement.style.transform = 'translateY(0)';
            }
        }, 50);

        setTimeout(() => {
            const toastElement = document.getElementById(toastId);
            if (toastElement) {
                toastElement.style.opacity = '0';
                toastElement.style.transform = 'translateY(-20px)';
                setTimeout(() => toastElement.remove(), 500);
            }
        }, 3500);
    }
}

function scrollChatToEnd() {
    const messagesContainer = document.getElementById('messagesArea');
    if (messagesContainer) {
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 20);
    }
}

function initializeJournalModalElements() {
    manualEntryModalJsEl = document.getElementById('manualEntryModal');
    manualEntryFormJsEl = document.getElementById('manualEntryForm');
    manualDateInputJsEl = document.getElementById('manualDate');
    addManualEntryButtonJsEl = document.getElementById('addManualEntryButton');
    cancelManualEntryButtonJsEl = document.getElementById('cancelManualEntryButton');

    if (manualEntryModalJsEl) {
        closeManualEntryModalButtonJsEl = manualEntryModalJsEl.querySelector('.modal-box form[method="dialog"] button.btn-ghost');
    }

    if (addManualEntryButtonJsEl && manualEntryModalJsEl) {
        addManualEntryButtonJsEl.addEventListener('click', () => {
            if (manualEntryFormJsEl) {
                manualEntryFormJsEl.reset();
            }
            if (manualDateInputJsEl) {
                manualDateInputJsEl.value = new Date().toISOString().split('T')[0];
            }
            if (typeof manualEntryModalJsEl.showModal === 'function') {
                manualEntryModalJsEl.showModal();
            } else {
                console.error("manualEntryModalJsEl.showModal is not a function. Modal element not found or DaisyUI not loaded correctly.");
            }
        });
    }

    if (cancelManualEntryButtonJsEl && manualEntryModalJsEl) {
        cancelManualEntryButtonJsEl.addEventListener('click', () => {
            if (typeof manualEntryModalJsEl.close === 'function') {
                manualEntryModalJsEl.close();
            }
        });
    }

    if (closeManualEntryModalButtonJsEl && manualEntryModalJsEl) {
         closeManualEntryModalButtonJsEl.addEventListener('click', (e) => {
            e.preventDefault();
            if (typeof manualEntryModalJsEl.close === 'function') {
                manualEntryModalJsEl.close();
            }
        });
    }

    if (manualEntryFormJsEl && manualEntryModalJsEl) {
        manualEntryFormJsEl.addEventListener('htmx:afterOnLoad', function(event) {
            if (event.detail.successful && event.target === manualEntryFormJsEl) {
                if (typeof manualEntryModalJsEl.close === 'function') {
                    manualEntryModalJsEl.close();
                }
                showToast("Journal entry added successfully!", "success");
            }
        });

        manualEntryFormJsEl.addEventListener('htmx:responseError', function(event) {
            if (event.target === manualEntryFormJsEl) {
                showToast("Error adding journal entry. Please try again.", "error");
            }
        });
    }
}

// ========================================
// GLOBAL EVENT LISTENERS
// ========================================

document.body.addEventListener('htmx:afterSwap', function(event) {
    // Scroll chat to end
    const messagesArea = document.getElementById('messagesArea');
    if (messagesArea && (event.detail.target === messagesArea || (event.detail.elt && messagesArea.contains(event.detail.elt)))) {
        scrollChatToEnd();
    }

    // Journal UI consistency check
    const journalList = document.getElementById('journalEntriesList');
    const noEntriesDiv = document.getElementById('noJournalEntries');
    const clearContainer = document.getElementById('clearAllJournalButton');

    if (journalList && noEntriesDiv && clearContainer) {
        const entryItemsCount = journalList.querySelectorAll('[id^="journal-entry-"]').length;

        if (entryItemsCount === 0) {
            noEntriesDiv.style.display = 'flex';
            clearContainer.style.display = 'none';
        } else {
            noEntriesDiv.style.display = 'none';
            clearContainer.style.display = 'block';
        }
    }
});

// ========================================
// INITIALIZATION
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    initializeScanAnimationElements();
    initializeChatAttachmentElements();
    initializeJournalModalElements();
    initializeChatHistoryElements();
    initializeChatMessageMonitoring();
    initializeChatHistory(); // Initialize with welcome message
    
    // Delay the start of the body scan animation by 4 seconds
    setTimeout(() => {
        startBodyScanAnimation();
    }, 4000);
    
    updateScanAnimationVisuals();
});

console.log("wellness_enhancements.js loaded (v3.0 - personal-info integration).");
