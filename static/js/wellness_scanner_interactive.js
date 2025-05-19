// static/js/wellness_scanner_interactive.js

document.addEventListener('DOMContentLoaded', () => {
    // Configuration (must match Python settings for consistency)
    const GRID_SQUARE_SIZE_PX = 20; 
    const HIGHLIGHT_DURATION_MS = 2000; // How long the square stays lit

    // Get the main SVG area where the grid is displayed
    const interactiveGridSVG = document.getElementById('interactiveGridArea');

    if (!interactiveGridSVG) {
        console.error('Error: The SVG element with ID "interactiveGridArea" was not found. Grid interaction will not work.');
        return;
    }

    /**
     * Handles the custom event to light up a grid square.
     * @param {CustomEvent} event - The event object, expected to have event.detail.x_cell and event.detail.y_cell.
     */
    function handleLightUpGridSquare(event) {
        if (!event.detail || typeof event.detail.x_cell === 'undefined' || typeof event.detail.y_cell === 'undefined') {
            console.warn('lightUpGridSquare event triggered without proper x_cell/y_cell data in event.detail:', event.detail);
            return;
        }

        const x_cell = parseInt(event.detail.x_cell, 10);
        const y_cell = parseInt(event.detail.y_cell, 10);

        console.log(`Received request to highlight grid cell: (col_index: ${x_cell}, row_index: ${y_cell})`);

        // Calculate pixel coordinates for the top-left of the cell
        const pixelX = x_cell * GRID_SQUARE_SIZE_PX;
        const pixelY = y_cell * GRID_SQUARE_SIZE_PX;

        // Create the highlight rectangle SVG element
        const highlightRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        highlightRect.setAttribute('x', pixelX);
        highlightRect.setAttribute('y', pixelY);
        highlightRect.setAttribute('width', GRID_SQUARE_SIZE_PX);
        highlightRect.setAttribute('height', GRID_SQUARE_SIZE_PX);
        
        // Style the highlight
        highlightRect.setAttribute('fill', 'rgba(255, 223, 0, 0.6)'); // Semi-transparent yellow
        highlightRect.setAttribute('stroke', 'orange');
        highlightRect.setAttribute('stroke-width', '1.5'); // Slightly thicker stroke for visibility
        highlightRect.setAttribute('class', 'grid-highlight-transient'); // Class for easy removal and potential CSS transition
        highlightRect.style.pointerEvents = 'none'; // Ensure it doesn't interfere with other interactions

        // Remove any previously added highlight to avoid multiple highlights
        const existingHighlights = interactiveGridSVG.querySelectorAll('.grid-highlight-transient');
        existingHighlights.forEach(hl => hl.remove());

        // Add the new highlight to the SVG
        interactiveGridSVG.appendChild(highlightRect);
        console.log(`Added highlight rect at (${pixelX}px, ${pixelY}px)`);

        // Set a timeout to remove the highlight after a specified duration
        setTimeout(() => {
            // Optional: Add a fade-out transition via CSS if desired before removing
            highlightRect.remove();
            console.log(`Removed highlight rect for cell (${x_cell}, ${y_cell})`);
        }, HIGHLIGHT_DURATION_MS);
        
        // Close the modal after processing
        const modal = document.getElementById('lightUpSquareModal');
        if (modal && typeof modal.close === 'function') {
            modal.close();
        }
    }

    // Listen for the custom event triggered by HTMX (via HX-Trigger header)
    document.body.addEventListener('lightUpGridSquare', handleLightUpGridSquare);

    // Handle opening the modal for "Light Up Square" button
    // This was previously in an inline script, moving it here for better organization.
    const openBtn = document.getElementById('openLightUpSquareModalButton');
    const modalElement = document.getElementById('lightUpSquareModal');
    if (openBtn && modalElement) {
        openBtn.addEventListener('click', () => modalElement.showModal());
    }
    
    // Handle the "Cancel" button inside the lightUpSquareModal specifically
    // The `**{'onclick': 'lightUpSquareModal.close()'}` on the cancel button in Python
    // is a good way, but this provides a JS alternative if that FT feature isn't available
    // or for more complex logic.
    // However, DaisyUI modals often close with form method="dialog" on a button or by pressing Esc.
    // The `**{'onclick': 'lightUpSquareModal.close()'}` is generally the most straightforward for a cancel button.
    // If the confirm button's hx_swap="innerHTML" targets the modal's content and returns empty,
    // that could also effectively "clear" the modal content, and then JS could close it.
    // For this iteration, we'll rely on the HX-Trigger to fire the event, and the JS event handler
    // will explicitly close the modal.

    console.log('Wellness scanner interactive JS loaded and event listeners attached.');
});