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

    // Event listeners for modal buttons
    if (confirmNarrowScanButtonEl && narrowScanModalEl && narrowScanInputEl) {
        confirmNarrowScanButtonEl.addEventListener('click', handleConfirmNarrowScan);
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

function handleConfirmNarrowScan() {
    if (!narrowScanInputEl || !mainAnatomySvgFtEl || !narrowScanModalEl) return;

    const searchTerm = narrowScanInputEl.value.trim().toLowerCase();
    if (!searchTerm) {
        showToast("Please enter a body part to scan.", "warning");
        return;
    }

    let foundPart = null;
    const allParts = mainAnatomySvgFtEl.querySelectorAll('.body-part');
    for (const part of allParts) {
        const partName = (part.dataset.name || part.id.replace(/_group/g, '').replace(/_/g, ' ')).toLowerCase();
        if (partName.includes(searchTerm)) {
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
        if (typeof narrowScanModalEl.close === 'function') {
            narrowScanModalEl.close();
        }
        showToast(`Narrow scan initiated for: ${foundPart.dataset.name || searchTerm}`, "success");
    } else {
        showToast(`Body part "${narrowScanInputEl.value}" not found. Please try a different term.`, "error");
    }
}

function startBodyScanAnimation() {
    console.log("startBodyScanAnimation called"); // Modified log for clarity
    clearAllEffects(); 

    globalScanLinePosition = SCAN_START_Y_VIEWBOX;
    globalScanLineDirection = 'down';
    globalIsLineScanning = true; 
    
    stopScanLineAnimationInterval(); 
    startScanLineAnimationInterval(); 
    updateScanAnimationVisuals(); 
}

function stopBodyScanAnimation() {
    console.log("stopBodyScanAnimation called"); // Modified log for clarity
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

document.addEventListener('DOMContentLoaded', () => {
    initializeScanAnimationElements(); 
    startBodyScanAnimation(); // ADD THIS LINE TO START SCAN ON PAGE LOAD
});

console.log("wellness_enhancements.js loaded (v2.7 - auto start scan).");
