// static/script.js
document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-upload');
    const fileNameSpan = document.getElementById('file-name');
    const uploadStatus = document.getElementById('upload-status');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const chatBox = document.getElementById('chat-box');

    // Update file name display
    fileInput.addEventListener('change', () => {
        fileNameSpan.textContent = fileInput.files.length > 0 ? fileInput.files[0].name : 'No file chosen';
    });

    // Handle file upload
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (fileInput.files.length === 0) {
            alert('Please select a PDF file to upload.');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        uploadStatus.textContent = 'Processing document...';
        uploadStatus.className = 'upload-status processing';

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            if (response.ok && result.success) {
                uploadStatus.textContent = result.message;
                uploadStatus.className = 'upload-status success';
                userInput.disabled = false;
                sendButton.disabled = false;
                appendMessage('Your document is ready. You can now ask questions.', 'assistant-message');
            } else {
                throw new Error(result.error || 'Unknown error occurred.');
            }
        } catch (error) {
            uploadStatus.textContent = `Error: ${error.message}`;
            uploadStatus.className = 'upload-status error';
        }
    });

    // Handle chat form submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = userInput.value.trim();
        if (!query) return;

        appendMessage(query, 'user-message');
        userInput.value = '';

        const assistantMessageElement = appendMessage('', 'assistant-message');
        const assistantParagraph = assistantMessageElement.querySelector('p');
        assistantParagraph.innerHTML = '<span class="blinking-cursor"></span>';

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullResponse = '';

            const cursor = assistantParagraph.querySelector('.blinking-cursor');
            if (cursor) cursor.remove();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.substring(6);
                        if (data === '[END_OF_STREAM]') return;
                        if (data.startsWith('[ERROR]')) {
                            fullResponse += `<span class="error-text">${data}</span>`;
                        } else {
                            fullResponse += data;
                        }
                        assistantParagraph.innerHTML = fullResponse;
                        chatBox.scrollTop = chatBox.scrollHeight;
                    }
                }
            }
        } catch (error) {
            assistantParagraph.innerHTML = `<span class="error-text">Error: ${error.message}</span>`;
        }
    });

    function appendMessage(text, className) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${className}`;
        const p = document.createElement('p');
        p.innerHTML = text;
        messageDiv.appendChild(p);
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
        return messageDiv;
    }

    // Add blinking cursor style
    const style = document.createElement('style');
    style.innerHTML = `
        .blinking-cursor { display: inline-block; width: 8px; height: 1em; background-color: var(--text-color); animation: blink 1s step-end infinite; }
        @keyframes blink { from, to { background-color: transparent } 50% { background-color: var(--text-color); } }
        .error-text { color: var(--error-color); font-weight: bold; }
    `;
    document.head.appendChild(style);
});