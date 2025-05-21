// wellness_enhancements.js

// --- SCANNER ANIMATION STATE & DOM ELEMENTS ---
const SCAN_START_Y_VIEWBOX = 32; 
const SCAN_END_Y_VIEWBOX = 165;  
const SCAN_SPEED_UNITS_PER_INTERVAL = 1.0; 

let globalScanLinePosition = SCAN_START_Y_VIEWBOX;
let globalScanLineDirection = 'down';
let globalIsLineScanning = false;
let globalScanLineAnimationInterval = null;

// New state for FT SVG outline pulsating
let globalIsFtBodyOutlinePulsating = false;

// New state for narrow scan
let globalNarrowScannedPartEl = null;

// DOM Element References
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
let attachImageButtonEl = null;
let attachDocumentButtonEl = null;
let chatFormEl = null;
let chatInputEl = null; 


// Function to initialize chat-related elements (call this in DOMContentLoaded)
function initializeChatAttachmentElements() {
    fileInputEl = document.getElementById('fileInput');
    stagedAttachmentsContainerEl = document.getElementById('stagedAttachmentsContainer');
    attachImageButtonEl = document.getElementById('attachImageButton');
    attachDocumentButtonEl = document.getElementById('attachDocumentButton');
    chatFormEl = document.getElementById('chatForm'); // Use the ID
    chatInputEl = document.getElementById('chatInput'); // Get chat input textarea

    if (attachImageButtonEl && fileInputEl) {
        attachImageButtonEl.addEventListener('click', () => {
            fileInputEl.accept = 'image/*';
            fileInputEl.multiple = true;
            fileInputEl.click();
            // Close dropdown (DaisyUI specific for dropdown focus)
            if (document.activeElement && document.activeElement instanceof HTMLElement) {
                document.activeElement.blur();
            }
        });
    }
    if (attachDocumentButtonEl && fileInputEl) {
        attachDocumentButtonEl.addEventListener('click', () => {
            fileInputEl.accept = '.pdf,.doc,.docx,.txt,.md';
            fileInputEl.multiple = true;
            fileInputEl.click();
            if (document.activeElement && document.activeElement instanceof HTMLElement) {
                document.activeElement.blur();
            }
        });
    }
    if (fileInputEl) {
        fileInputEl.addEventListener('change', handleFileSelection);
    }

    if (chatFormEl) {
        // IMPORTANT: Override HTMX's FormData construction to include our staged files
        chatFormEl.addEventListener('htmx:configRequest', function(event) {
            const formData = new FormData();
            // Append chat input text
            if (chatInputEl) {
                formData.append('chatInput', chatInputEl.value);
            }

            // Append staged files
            let hasFiles = false;
            stagedFilesData.forEach(stagedFile => {
                formData.append('files', stagedFile.file, stagedFile.file.name); // 'files' is the name server expects
                hasFiles = true;
            });

            event.detail.parameters = formData; // This is how you set the body for HTMX POST/PUT with FormData

            // If files are present, HTMX needs to know it's multipart.
            // The browser usually sets the Content-Type correctly for FormData (including boundary).
            // We might need to tell HTMX not to set its default Content-Type.
            if (hasFiles) {
                 // Let the browser set the Content-Type for FormData
                delete event.detail.headers['Content-Type'];
            }
        });

        // Clear staged files and input after successful HTMX request
        chatFormEl.addEventListener('htmx:afterRequest', function(event) {
            if (event.detail.successful) {
                clearStagedFilesAndInput();
                if (chatInputEl) { // Also clear the textarea
                   // chatInputEl.value = ''; // The backend already returns a cleared input via OOB
                   // autoResizeTextarea(chatInputEl); // Resize if needed
                }
            }
        });
    }
}

function handleFileSelection(event) {
    const files = event.target.files;
    if (!files) return;
    const maxFiles = 5;
    const maxSizePerFile = 5 * 1024 * 1024; // 5MB

    if (stagedFilesData.length + files.length > maxFiles) {
        showToast(`You can attach a maximum of ${maxFiles} files.`, 'warning');
        event.target.value = null; // Clear the input
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
    event.target.value = null; // Reset file input to allow selecting the same or more files
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
        attachmentEl.className = 'staged-attachment-item flex items-center justify-between p-1.5 bg-base-300/50 rounded text-xs mb-1 group';
        attachmentEl.dataset.fileId = stagedFile.id;

        const fileInfo = document.createElement('div');
        fileInfo.className = 'flex items-center overflow-hidden mr-2 flex-grow';

        const icon = document.createElement('span');
        icon.className = 'material-symbols-outlined emoji-icon text-lg mr-1.5 text-primary/80 flex-shrink-0';
        icon.textContent = stagedFile.type === 'image' ? 'image' : 'article';

        const nameAndSizeDiv = document.createElement('div');
        nameAndSizeDiv.className = 'flex flex-col overflow-hidden';

        const name = document.createElement('span');
        name.className = 'truncate text-base-content/90 text-xs';
        name.textContent = stagedFile.file.name;
        name.title = stagedFile.file.name;
        
        const size = document.createElement('span');
        size.className = 'text-base-content/70 text-xxs'; // Ensure text-xxs is defined or use text-xs
        size.textContent = `${(stagedFile.file.size / 1024).toFixed(1)} KB`;

        nameAndSizeDiv.appendChild(name);
        nameAndSizeDiv.appendChild(size);
        
        fileInfo.appendChild(icon);
        fileInfo.appendChild(nameAndSizeDiv);

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-xs btn-ghost btn-circle text-error opacity-50 group-hover:opacity-100 transition-opacity flex-shrink-0';
        removeBtn.innerHTML = '<span class="material-symbols-outlined emoji-icon text-base">close</span>';
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
    // No need to manipulate fileInputEl.value here as we are using FormData from stagedFilesData
}

function clearStagedFilesAndInput() {
    stagedFilesData = [];
    if (fileInputEl) {
        fileInputEl.value = null; // Clear the actual file input as a good measure
    }
    if (stagedAttachmentsContainerEl) {
      renderStagedAttachments(); // This will hide the container if empty
    }
}



function initializeScanAnimationElements() {
    scanLineAnimationGroupRawEl = document.getElementById('scanLineAnimationGroupRaw');
    scanLineAnimationElementRawEl = document.getElementById('scanLineAnimationElementRaw');
    scanLineHighlightAnimationElementRawEl = document.getElementById('scanLineHighlightAnimationElementRaw');
    
    generalScannerStatusTextEl = document.getElementById('scannerStatusText');
    generalScannerStatusIconContainerEl = document.getElementById('scannerStatusIconContainer');

    mainAnatomySvgFtEl = document.getElementById('mainAnatomySvgFT');

    // Caching for narrow scan modal elements
    narrowScanModalEl = document.getElementById('narrowScanModal');
    narrowScanInputEl = document.getElementById('narrowScanInput');
    confirmNarrowScanButtonEl = document.getElementById('confirmNarrowScanButton');
    closeNarrowScanModalButtonEl = document.getElementById('closeNarrowScanModalButton');
    
    console.log("Scan animation elements initialized:",
        !!scanLineAnimationGroupRawEl,
        !!generalScannerStatusTextEl,
        !!mainAnatomySvgFtEl,
        !!narrowScanModalEl
    );

    // Event listeners for modal buttons (manual narrow scan)
    if (confirmNarrowScanButtonEl && narrowScanModalEl && narrowScanInputEl) {
        confirmNarrowScanButtonEl.addEventListener('click', handleConfirmManualNarrowScan); // Renamed for clarity
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

/**
 * Initiates a narrow scan animation on a specified body part.
 * @param {string} partName - The name of the body part to scan (e.g., "Head", "Lungs").
 */
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
        // Optionally, fall back to a general scan or idle state
        // stopBodyScanAnimation(); // Or some other default state
    }
}


// Renamed original function to avoid confusion with direct narrow scan trigger
function handleConfirmManualNarrowScan() {
    if (!narrowScanInputEl || !narrowScanModalEl) return;
    const partNameFromInput = narrowScanInputEl.value;
    triggerNarrowScanForPart(partNameFromInput); // Use the new direct function
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
    // Do not clear globalNarrowScannedPartEl or globalIsFtBodyOutlinePulsating here,
    // as stop might be called to transition to a narrow scan or glow.
    // clearAllEffects() should be called explicitly if a full reset is needed.
    updateScanAnimationVisuals();
}

function toggleBodyGlowEffect() {
    console.log("toggleBodyGlowEffect called (for FT SVG outline pulsate)");
    
    const wasPulsating = globalIsFtBodyOutlinePulsating;
    clearAllEffects(); // Clear other effects before toggling glow

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

/**
 * Central command executor for body scanner animations.
 * @param {string} command - The command to execute (e.g., "START_SCAN", "STOP_SCAN", "FULL_BODY_GLOW", or a specific body part name).
 */
function executeBodyScannerCommand(command) {
    console.log(`Executing body scanner command: ${command}`);
    if (!command || command.trim() === "" || command.toLowerCase() === "idle") {
        // Optionally, set to idle or do nothing if command is "idle"
        // stopBodyScanAnimation(); // Example: go to idle
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
            // Note: STOP_SCAN usually means go to idle. If an LLM says "stop scan" then "scan head",
            // the "scan head" command will override.
            break;
        case "FULL_BODY_GLOW":
            toggleBodyGlowEffect();
            break;
        default:
            // Assuming any other non-empty command is a body part name for narrow scan
            triggerNarrowScanForPart(command);
            break;
    }
}


// Basic Toast Function (if not already globally available)
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


// --- CHAT AUTO-SCROLLING LOGIC (REVISED) ---
function scrollChatToEnd() {
    const messagesContainer = document.getElementById('messagesArea');
    if (messagesContainer) {
        // Using a very short timeout defers the scroll operation until after the
        // current JavaScript execution stack has cleared and the browser has had a chance
        // to process DOM changes and reflows. This often helps get the correct scrollHeight.
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 20); // 0ms is often enough, but you can try 50ms or 100ms if issues persist
    }
}

document.body.addEventListener('htmx:afterSwap', function(event) {
    const messagesArea = document.getElementById('messagesArea');

    if (messagesArea) {
        let shouldScroll = false;

        // Case 1: The direct target of the swap is the messagesArea itself
        // (This happens when user_chat_bubble and typing_loader_trigger are appended)
        if (event.detail.target === messagesArea) {
            shouldScroll = true;
        }
        // Case 2: An element *inside* messagesArea was swapped/replaced
        // (This happens when typing_loader_trigger is replaced by typing_indicator_bubble,
        // and then typing_indicator_bubble is replaced by the ai_chat_bubble_component)
        else if (event.detail.elt && messagesArea.contains(event.detail.elt)) {
            shouldScroll = true;
        }

        if (shouldScroll) {
            scrollChatToEnd();
        }
    }
});


document.addEventListener('DOMContentLoaded', () => {
    initializeScanAnimationElements();
    startBodyScanAnimation(); // Auto-start removed, will be command-driven
    updateScanAnimationVisuals(); // Ensure initial idle state is shown
    initializeChatAttachmentElements(); // Call the new initializer
});



console.log("wellness_enhancements.js loaded (v2.8 - command executor).");
