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
// We keep chatInputEl for initial setup, but will rely on event.target within htmx:configRequest
let chatInputEl = null;

// --- WELLNESS JOURNAL UI (Manual Modal Handling) ---
let manualEntryModalJsEl = null;
let manualEntryFormJsEl = null; // The form that will be submitted via HTMX
let manualDateInputJsEl = null;
let addManualEntryButtonJsEl = null;
let cancelManualEntryButtonJsEl = null; // The "Cancel" button inside the modal
let closeManualEntryModalButtonJsEl = null; // The 'X' button inside the modal-box



// Function to initialize chat-related elements (call this in DOMContentLoaded)
function initializeChatAttachmentElements() {
    fileInputEl = document.getElementById('fileInput');
    stagedAttachmentsContainerEl = document.getElementById('stagedAttachmentsContainer');
    attachImageButtonEl = document.getElementById('attachImageButton');
    attachDocumentButtonEl = document.getElementById('attachDocumentButton');
    chatFormEl = document.getElementById('chatForm'); // Use the ID
    chatInputEl = document.getElementById('chatInput'); // Initial reference

    if (attachImageButtonEl && fileInputEl) {
        attachImageButtonEl.addEventListener('click', () => {
            fileInputEl.accept = 'image/*';
            fileInputEl.multiple = true;
            fileInputEl.click();
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
        // IMPORTANT: Override HTMX's FormData construction
        chatFormEl.addEventListener('htmx:configRequest', function(event) {
            const formData = new FormData();

            // *** MODIFICATION START ***
            // Get the chatInput element directly from the form that triggered the event (event.target).
            // This ensures we get the *current* input, even after OOB swaps.
            // The 'name' attribute of the textarea is 'chatInput'.
            const currentChatInputElement = event.target.elements.chatInput;

            if (currentChatInputElement) {
                formData.append('chatInput', currentChatInputElement.value);
            } else {
                // Fallback or error if chatInput is not found by name.
                // This might happen if the ID is "chatInput" but the name attribute is different or missing.
                // However, your Python OOB swap correctly sets name="chatInput".
                console.warn("chatInput element not found by name in the form during htmx:configRequest. Trying by ID from global scope as fallback.");
                const currentChatInputById = document.getElementById('chatInput'); // Re-fetch by ID just in case
                if (currentChatInputById) {
                     formData.append('chatInput', currentChatInputById.value);
                } else if (chatInputEl) { // Absolute fallback to the initially captured global
                    formData.append('chatInput', chatInputEl.value);
                    console.warn("Fell back to globally scoped chatInputEl. This might send stale data if OOB swaps occurred.");
                } else {
                    console.error("Completely unable to find chatInput to append to FormData.");
                }
            }
            // *** MODIFICATION END ***

            // Append staged files
            let hasFiles = false;
            stagedFilesData.forEach(stagedFile => {
                // Ensure your server-side code expects files under the name "files"
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
                // The textarea itself is cleared by an OOB swap from the server,
                // so no need to do chatInputEl.value = '' here.
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
    event.target.value = null; // Reset file input
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
        size.className = 'text-base-content/70 text-xxs';
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
            alert(message); // Fallback if toast container is missing
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

    // Get the 'X' button inside the modal-box of the manualEntryModal
    if (manualEntryModalJsEl) {
        closeManualEntryModalButtonJsEl = manualEntryModalJsEl.querySelector('.modal-box #closeManualEntryModalButtonInternal'); 
        // Note: The ID in main.py for this button was 'closeManualEntryModalButtonInternal'
        // Ensure this matches the ID you have in the FT component for that button.
        // If you used `id="closeManualEntryModalButton"` in FT, change selector here or ID in FT.
        // For now, assuming 'closeManualEntryModalButtonInternal' as per Python snippet.
        // If it's simply the one in the <form method="dialog">, DaisyUI handles it.
        // The python code has: Button(Span("close", cls="material-icons emoji-icon"), id="closeManualEntryModalButtonInternal", ... )
    }


    if (addManualEntryButtonJsEl && manualEntryModalJsEl) {
        addManualEntryButtonJsEl.addEventListener('click', () => {
            if (manualEntryFormJsEl) {
                manualEntryFormJsEl.reset(); // Reset form fields
            }
            if (manualDateInputJsEl) {
                // Set default date to today
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

    // This handles the 'X' button inside the modal box if it's not part of a method="dialog" form
    if (closeManualEntryModalButtonJsEl && manualEntryModalJsEl) {
         closeManualEntryModalButtonJsEl.addEventListener('click', (e) => {
            e.preventDefault(); // Good practice if it's a button not meant to submit
            if (typeof manualEntryModalJsEl.close === 'function') {
                manualEntryModalJsEl.close();
            }
        });
    }

    // Handle HTMX form submission events for the manual entry form
    if (manualEntryFormJsEl && manualEntryModalJsEl) {
        manualEntryFormJsEl.addEventListener('htmx:afterOnLoad', function(event) {
            // htmx:afterOnLoad is triggered after the new content has been loaded and processed.
            if (event.detail.successful && event.target === manualEntryFormJsEl) {
                if (typeof manualEntryModalJsEl.close === 'function') {
                    manualEntryModalJsEl.close(); // Close modal on successful HTMX submission
                }
                showToast("Journal entry added successfully!", "success");
                // The server response for ADD should include OOB swaps for placeholder/clear button.
                // The global htmx:afterSwap listener will also run to ensure consistency.
            }
        });

        manualEntryFormJsEl.addEventListener('htmx:responseError', function(event) {
            if (event.target === manualEntryFormJsEl) {
                showToast("Error adding journal entry. Please try again.", "error");
                // Optionally, keep the modal open or provide more specific error feedback.
            }
        });
    }
}




document.body.addEventListener('htmx:afterSwap', function(event) {
    // --- Scroll chat to end (existing logic) ---
    const messagesArea = document.getElementById('messagesArea');
    if (messagesArea && (event.detail.target === messagesArea || (event.detail.elt && messagesArea.contains(event.detail.elt)))) {
        scrollChatToEnd(); // Assuming scrollChatToEnd is defined
    }

    // --- Journal UI consistency check ---
    const journalList = document.getElementById('journalEntriesList');
    const noEntriesDiv = document.getElementById('noJournalEntries');
    const clearContainer = document.getElementById('clearJournalContainer');

    if (journalList && noEntriesDiv && clearContainer) {
        // Count children that are actual entries (have an ID starting with 'journal-entry-')
        // This ensures we're counting rendered entry elements.
        const entryItemsCount = journalList.querySelectorAll('[id^="journal-entry-"]').length;

        if (entryItemsCount === 0) {
            noEntriesDiv.style.display = 'flex';
            clearContainer.style.display = 'none';
        } else {
            noEntriesDiv.style.display = 'none';
            clearContainer.style.display = 'flex';
        }
    }
});


document.addEventListener('DOMContentLoaded', () => {
    initializeScanAnimationElements();
    // Delay the start of the body scan animation by 2 seconds
    setTimeout(() => {
        startBodyScanAnimation();
    }, 4000); // 2000 milliseconds = 2 seconds
    updateScanAnimationVisuals(); // Ensure initial idle state is shown
    initializeChatAttachmentElements();
    initializeJournalModalElements(); // <--- ADD THIS CALL
});



console.log("wellness_enhancements.js loaded (v2.9 - chatInput fix).");
