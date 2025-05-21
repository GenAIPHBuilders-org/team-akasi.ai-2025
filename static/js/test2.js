// --- wellness_enhancements.js ---

// (Keep existing global variables and DOM element variables)
let stagedFilesData = []; // Holds { id, file: FileObject, type: 'image'/'document' }

// (Keep existing DOM element variables, ensure these are added/updated in your init)
let fileInputEl = null;
let stagedAttachmentsContainerEl = null;
let attachImageButtonEl = null;
let attachDocumentButtonEl = null;
let chatFormEl = null; // Reference to the <form id="chatForm">
let chatInputEl = null; // Reference to the <textarea id="chatInput">

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

// --- Ensure this initialization runs ---
document.addEventListener('DOMContentLoaded', () => {
    // ... your existing initializeScanAnimationElements(); and other initializations ...
    initializeChatAttachmentElements(); // Call the new initializer
    // ...
});

// (Keep your existing showToast, scanner logic, chat rendering logic, etc.)
// Make sure your existing autoResizeTextarea is available.