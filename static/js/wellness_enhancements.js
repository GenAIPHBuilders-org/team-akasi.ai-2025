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
// ANIMATION SLOWDOWN MANAGEMENT
// ========================================

let animationSlowdownActive = false;
let slowdownTimeouts = [];

function slowDownAkasiAnimations() {
    if (animationSlowdownActive) return; // Prevent multiple simultaneous slowdowns
    
    animationSlowdownActive = true;
    
    // Clear any existing timeouts
    slowdownTimeouts.forEach(timeout => clearTimeout(timeout));
    slowdownTimeouts = [];
    
    const akasiComponent = document.querySelector('.akasi-component');
    const medicalIcon = document.querySelector('.akasi-floating-ball .medical-icon');
    const heartIcon = document.querySelector('.akasi-floating-ball .heart-icon');
    
    // Phase 1: Start slowing down (immediate)
    if (akasiComponent) {
        akasiComponent.classList.add('slowing-down');
    }
    
    if (medicalIcon) {
        medicalIcon.classList.add('slowing-down');
    }
    
    if (heartIcon) {
        heartIcon.classList.add('slowing-down');
    }
    
    // Phase 2: Very slow (after 2 seconds)
    const phase2Timeout = setTimeout(() => {
        if (akasiComponent) {
            akasiComponent.classList.remove('slowing-down');
            akasiComponent.classList.add('very-slow');
        }
        
        if (medicalIcon) {
            medicalIcon.classList.remove('slowing-down');
            medicalIcon.classList.add('very-slow');
        }
        
        if (heartIcon) {
            heartIcon.classList.remove('slowing-down');
            heartIcon.classList.add('very-slow');
        }
    }, 2000);
    slowdownTimeouts.push(phase2Timeout);
    
    // Phase 3: Stopping animation (after 5 seconds total)
    const phase3Timeout = setTimeout(() => {
        if (akasiComponent) {
            akasiComponent.classList.remove('very-slow');
            akasiComponent.classList.add('stopping');
        }
        
        if (medicalIcon) {
            medicalIcon.classList.remove('very-slow');
            medicalIcon.classList.add('stopping');
        }
        
        if (heartIcon) {
            heartIcon.classList.remove('very-slow');
            heartIcon.classList.add('stopping');
        }
    }, 5000);
    slowdownTimeouts.push(phase3Timeout);
    
    // Phase 4: Completely stopped (after 7.5 seconds total)
    const phase4Timeout = setTimeout(() => {
        if (akasiComponent) {
            akasiComponent.classList.remove('stopping');
            akasiComponent.classList.add('stopped');
        }
        
        if (medicalIcon) {
            medicalIcon.classList.remove('stopping');
            medicalIcon.classList.add('stopped');
        }
        
        if (heartIcon) {
            heartIcon.classList.remove('stopping');
            heartIcon.classList.add('stopped');
        }
        
        animationSlowdownActive = false;
    }, 7500);
    slowdownTimeouts.push(phase4Timeout);
}



// ========================================
// CHAT HISTORY FUNCTIONALITY (SIMPLIFIED)
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
        renderChatHistory();
        chatHistoryOverlay.style.display = 'block';
        chatHistoryOverlay.offsetHeight;
        chatHistoryOverlay.classList.add('show');
        
        setTimeout(() => {
            if (chatMessages) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }, 100);
    }
}

function hideChatHistory() {
    if (chatHistoryOverlay) {
        chatHistoryOverlay.classList.remove('show');
        setTimeout(() => {
            chatHistoryOverlay.style.display = 'none';
        }, 300);
    }
}

function updateChatHistoryIfOpen() {
    if (chatHistoryOverlay && 
        chatHistoryOverlay.style.display === 'block' && 
        chatHistoryOverlay.classList.contains('show')) {
        
        renderChatHistory();
        setTimeout(() => {
            if (chatMessages) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }, 50);
    }
}

// ========================================
// SIMPLIFIED CHAT MONITORING
// ========================================

function initializeChatMessageMonitoring() {
    // Monitor form submissions for user messages
    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
        chatForm.addEventListener('submit', function(event) {
            const formData = new FormData(chatForm);
            const userMessage = formData.get('chatInput');
            if (userMessage && userMessage.trim()) {
                addMessageToHistory('user', userMessage.trim());
                
                // Add typing indicator to chat history
                setTimeout(() => {
                    addMessageToHistory('akasi', 'Akasi is typing...');
                }, 500);
                
                slowDownAkasiAnimations();
            }
        });
    }

    // Monitor speech bubble content changes directly
    const speechContent = document.getElementById('akasi-speech-content');
    if (speechContent) {
        const observer = new MutationObserver(() => {
            const currentText = speechContent.textContent?.trim();
            if (currentText && 
                currentText.length > 10 && 
                !currentText.includes('Akasi is typing') &&
                !currentText.includes('I didn\'t receive any message') &&
                !isMessageAlreadyInHistory(currentText)) {
                
                // Replace the last "typing" message if it exists
                if (conversationHistory.length > 0 && 
                    conversationHistory[conversationHistory.length - 1].message === 'Akasi is typing...') {
                    conversationHistory[conversationHistory.length - 1] = {
                        type: 'akasi',
                        message: currentText,
                        timestamp: new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})
                    };
                } else {
                    addMessageToHistory('akasi', currentText);
                }
                
                // Save to localStorage
                localStorage.setItem('wellness_chat_history', JSON.stringify(conversationHistory));
                updateChatHistoryIfOpen();
            }
        });
        
        observer.observe(speechContent, {
            childList: true,
            subtree: true,
            characterData: true
        });
    }
}

function isMessageAlreadyInHistory(messageText) {
    return conversationHistory.some(entry => entry.message === messageText);
}

// ========================================
// BODY SCANNER MODAL FUNCTIONALITY
// ========================================

function showBodyScannerModal() {
    if (bodyScannerOverlay) {
        bodyScannerOverlay.style.display = 'block';
        bodyScannerOverlay.offsetHeight;
        bodyScannerOverlay.classList.add('show');
        
        setTimeout(() => {
            startBodyScanAnimation();
        }, 500);
    }
}

function hideBodyScannerModal() {
    if (bodyScannerOverlay) {
        bodyScannerOverlay.classList.remove('show');
        
        setTimeout(() => {
            bodyScannerOverlay.style.display = 'none';
            stopBodyScanAnimation();
        }, 300);
    }
}

// ========================================
// SPEECH BUBBLE FORM ENHANCEMENTS
// ========================================

function initializeSpeechBubbleForm() {
    // Enter key handling
    document.addEventListener('keypress', (e) => {
        const target = e.target;
        if (target && target.id === 'chatInput' && e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const chatForm = document.getElementById('chatForm');
            if (chatForm) {
                chatForm.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
            }
        }
    });
    
    // Auto-resize functionality
    document.addEventListener('input', (e) => {
        const target = e.target;
        if (target && target.id === 'chatInput') {
            autoResizeTextarea(target);
        }
    });
}

function initializeAnimationControlListeners() {
    // Listen for send button clicks
    document.addEventListener('click', function(event) {
        if (event.target.closest('.send-button') || 
            event.target.closest('#sendButton') ||
            (event.target.closest('button[type="submit"]') && event.target.closest('#chatForm'))) {
            
            const form = event.target.closest('form');
            if (form) {
                const chatInput = form.querySelector('#chatInput') || form.querySelector('[name="chatInput"]');
                if (chatInput && chatInput.value && chatInput.value.trim()) {
                    slowDownAkasiAnimations();
                }
            }
        }
    });
}

// Auto-resize function for speech bubble textarea
function autoResizeTextarea(textarea) {
    if (!textarea) return;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.max(textarea.scrollHeight, 44)}px`;
}

function initializeChatAttachmentElements() {
    fileInputEl = document.getElementById('fileInput');
    stagedAttachmentsContainerEl = document.getElementById('stagedAttachmentsContainer');
    chatInputEl = document.getElementById('chatInput');
    
    // Find the chat form
    chatFormEl = document.getElementById('chatForm') || 
                 document.querySelector('form[hx-post*="send_chat_speech_bubble"]') ||
                 document.querySelector('form[action*="send_chat_speech_bubble"]') ||
                 document.querySelector('.chat-form-wrapper').closest('form');

    // File input change listener
    if (fileInputEl) {
        fileInputEl.addEventListener('change', handleFileSelection);
    }

    if (chatFormEl) {
        // Override HTMX's FormData construction
        chatFormEl.addEventListener('htmx:configRequest', function(event) {
            const formData = new FormData();

            // Get the chatInput element
            const currentChatInputElement = event.target.elements.chatInput;

            if (currentChatInputElement) {
                formData.append('chatInput', currentChatInputElement.value);
            } else {
                const currentChatInputById = document.getElementById('chatInput');
                if (currentChatInputById) {
                     formData.append('chatInput', currentChatInputById.value);
                } else if (chatInputEl) {
                    formData.append('chatInput', chatInputEl.value);
                }
            }

            // Append staged files
            stagedFilesData.forEach(stagedFile => {
                formData.append('files', stagedFile.file, stagedFile.file.name);
            });

            event.detail.parameters = formData;

            if (stagedFilesData.length > 0) {
                delete event.detail.headers['Content-Type'];
            }
        });

        // Clear staged files after successful request
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
        attachmentEl.className = 'staged-attachment-item';
        attachmentEl.dataset.fileId = stagedFile.id;

        const fileInfo = document.createElement('div');
        fileInfo.className = 'attachment-file-info';

        const icon = document.createElement('span');
        icon.className = 'material-icons';
        
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
        nameAndSizeDiv.className = 'attachment-info';

        const name = document.createElement('span');
        name.className = 'attachment-name';
        name.textContent = stagedFile.file.name;
        name.title = stagedFile.file.name;

        const size = document.createElement('span');
        size.className = 'attachment-size';
        size.textContent = `${(stagedFile.file.size / 1024).toFixed(1)} KB`;

        nameAndSizeDiv.appendChild(name);
        nameAndSizeDiv.appendChild(size);

        fileInfo.appendChild(icon);
        fileInfo.appendChild(nameAndSizeDiv);

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'remove-btn';
        removeBtn.innerHTML = '<span class="material-icons">close</span>';
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
    if (!mainAnatomySvgFtEl) {
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
    clearAllEffects();

    globalScanLinePosition = SCAN_START_Y_VIEWBOX;
    globalScanLineDirection = 'down';
    globalIsLineScanning = true;

    stopScanLineAnimationInterval();
    startScanLineAnimationInterval();
    updateScanAnimationVisuals();
}

function stopBodyScanAnimation() {
    globalIsLineScanning = false;
    stopScanLineAnimationInterval();
    updateScanAnimationVisuals();
}

function toggleBodyGlowEffect() {
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
    if (!command || command.trim() === "" || command.toLowerCase() === "idle") {
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

    // Initialize finish journal button to close modal first
    const finishJournalButton = document.getElementById('finishJournalButton');
    if (finishJournalButton) {
        finishJournalButton.addEventListener('click', function(event) {
            // Close the body scanner modal first
            hideBodyScannerModal();
            // The HTMX request will proceed after the click event
        });
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
    // Initialize all components
    initializeScanAnimationElements();
    initializeChatAttachmentElements();
    initializeJournalModalElements();
    initializeChatHistoryElements();
    initializeChatMessageMonitoring();
    initializeSpeechBubbleForm();
    initializeAnimationControlListeners();
    initializeChatHistory();
    
    // Delay the start of the body scan animation by 4 seconds
    setTimeout(() => {
        startBodyScanAnimation();
    }, 4000);
    
    updateScanAnimationVisuals();
});

console.log("wellness_enhancements.js loaded (v3.4 - simplified chat history).");
