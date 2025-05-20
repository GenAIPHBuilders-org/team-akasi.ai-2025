// wellness_enhancements.js

// --- SCANNER ANIMATION STATE & DOM ELEMENTS ---
const SCAN_START_Y_VIEWBOX = 32; // Approx. middle of cells 56-65 (scaled to 0-200 viewBox)
const SCAN_END_Y_VIEWBOX = 165;  // Approx. middle of cells 362-371 (scaled to 0-200 viewBox)
const SCAN_SPEED_UNITS_PER_INTERVAL = 1.0; // Speed of scan line in viewBox units per interval

let globalScanLinePosition = SCAN_START_Y_VIEWBOX;
let globalScanLineDirection = 'down';
let globalIsLineScanning = false;
let globalScanLineAnimationInterval = null;

// New state for FT SVG outline pulsating
let globalIsFtBodyOutlinePulsating = false;

// New state for narrow scan
let globalNarrowScannedPartEl = null; // To store the element currently undergoing narrow scan

// DOM Element References
let scanLineAnimationGroupRawEl = null;
let scanLineAnimationElementRawEl = null;
let scanLineHighlightAnimationElementRawEl = null;
let mainAnatomySvgFtEl = null; // For the main FT-generated SVG
let generalScannerStatusTextEl = null;
let generalScannerStatusIconContainerEl = null;
let narrowScanModalEl = null;
let narrowScanInputEl = null;
let confirmNarrowScanButtonEl = null;
let closeNarrowScanModalButtonEl = null;


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


// --- CHAT AUTO-SCROLLING LOGIC ---
function scrollChatToEnd() {
    const messagesEndRef = document.getElementById('messagesEndRef');
    if (messagesEndRef) {
        messagesEndRef.scrollIntoView({ behavior: 'smooth' });
    }
}

document.body.addEventListener('htmx:afterSwap', function(event) {
    const messagesArea = document.getElementById('messagesArea');

    if (messagesArea) {
        if (event.detail.target === messagesArea) {
            setTimeout(scrollChatToEnd, 50);
        }
        else if (event.detail.elt && messagesArea.contains(event.detail.elt)) {
             setTimeout(scrollChatToEnd, 50);
        }
    }
});


document.addEventListener('DOMContentLoaded', () => {
    initializeScanAnimationElements();
    // startBodyScanAnimation(); // Auto-start removed, will be command-driven
    updateScanAnimationVisuals(); // Ensure initial idle state is shown
});



console.log("wellness_enhancements.js loaded (v2.8 - command executor).");
