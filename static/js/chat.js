// ========== DOM ELEMENTS ==========
const messageInput = document.getElementById('messageInput');
const chatForm = document.getElementById('chatForm');
const messagesContainer = document.getElementById('messagesContainer');
const uploadBtn = document.getElementById('uploadBtn');
const fileInput = document.getElementById('fileInput');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');
const clearDocumentBtn = document.getElementById('clearDocumentBtn');
const documentsList = document.getElementById('documentsList');
const noDocumentsMsg = document.getElementById('noDocumentsMsg');
const questionsList = document.getElementById('questionsList');
const refreshQuestionsBtn = document.getElementById('refreshQuestionsBtn');
const sendBtn = document.getElementById('sendBtn');
const chunkSizeSlider = document.getElementById('chunkSizeSlider');
const chunkOverlapSlider = document.getElementById('chunkOverlapSlider');
const chunkSizeValue = document.getElementById('chunkSizeValue');
const chunkOverlapValue = document.getElementById('chunkOverlapValue');
const applyChunkBtn = document.getElementById('applyChunkBtn');
const resetChunkBtn = document.getElementById('resetChunkBtn');
const chunkStatus = document.getElementById('chunkStatus');

// ========== STATE ==========
let messages = [];
let currentDocument = null;
let questionHistory = [];
let isProcessing = false;

// ========== HELPER FUNCTIONS ==========
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getCurrentTimestamp() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// ========== RENDER FUNCTIONS ==========
function renderMessages() {
    if (!messagesContainer) return;
    
    messagesContainer.innerHTML = '';
    messages.forEach((message, index) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} message-animation`;
        messageDiv.setAttribute('data-message-id', message.id);
        messageDiv.setAttribute('data-message-index', index);
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = `max-w-2xl ${
            message.role === 'user'
                ? 'bg-black text-white'
                : 'bg-white border border-black text-black'
        } rounded-2xl px-5 py-3`;
        
        bubbleDiv.innerHTML = `
            <p class="whitespace-pre-wrap">${escapeHtml(message.content)}</p>
            <p class="text-xs mt-2 ${message.role === 'user' ? 'text-gray-300' : 'text-black'}">
                ${escapeHtml(message.timestamp)}
            </p>
        `;
        
        messageDiv.appendChild(bubbleDiv);
        messagesContainer.appendChild(messageDiv);
    });
    
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addMessage(role, content, messageId = null) {
    const newMessage = {
        id: messageId || Date.now().toString(),
        role: role,
        content: content,
        timestamp: getCurrentTimestamp()
    };
    messages.push(newMessage);
    renderMessages();
    return newMessage.id;
}

function renderDocuments() {
    if (!documentsList) return;
    
    if (currentDocument) {
        if (noDocumentsMsg) noDocumentsMsg.style.display = 'none';
        
        const fileExt = currentDocument.name?.split('.').pop().toLowerCase() || 'pdf';
        const isDocx = fileExt === 'docx';
        const bgColor = isDocx ? 'bg-blue-600' : 'bg-green-600';
        const borderColor = isDocx ? 'border-blue-500' : 'border-green-500';
        const bgLight = isDocx ? 'bg-blue-50' : 'bg-green-50';
        const fileTypeDisplay = isDocx ? 'DOCX' : 'PDF';
        
        const fileIcon = isDocx ? 
            `<svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>` :
            `<svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path></svg>`;
        
        documentsList.innerHTML = `
            <div class="p-4 rounded-lg border ${borderColor} ${bgLight} document-animation">
                <div class="flex items-start gap-3">
                    <div class="w-10 h-10 rounded-lg ${bgColor} flex items-center justify-center flex-shrink-0">
                        ${fileIcon}
                    </div>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm font-medium truncate mb-1 text-gray-900">${escapeHtml(currentDocument.name)}</p>
                        <div class="flex items-center justify-between text-xs text-gray-600">
                            <span>${fileTypeDisplay}</span>
                            <span>${escapeHtml(currentDocument.size)}</span>
                        </div>
                        <div class="mt-2 text-xs ${isDocx ? 'text-blue-600' : 'text-green-600'}">✓ Đã sẵn sàng</div>
                    </div>
                </div>
            </div>
        `;
    } else {
        if (noDocumentsMsg) noDocumentsMsg.style.display = 'block';
        documentsList.innerHTML = '';
        documentsList.appendChild(noDocumentsMsg);
    }
}

function renderRecentQuestions() {
    if (!questionsList) return;
    
    if (questionHistory.length === 0) {
        questionsList.innerHTML = `<div class="text-center text-gray-500 text-sm py-8">Chưa có câu hỏi nào</div>`;
        return;
    }
    
    questionsList.innerHTML = '';
    const recentQuestions = [...questionHistory].reverse().slice(0, 15);
    
    recentQuestions.forEach((q, idx) => {
        const questionDiv = document.createElement('div');
        questionDiv.className = 'question-item p-3 rounded-lg border border-black hover:bg-gray-100 cursor-pointer transition-colors';
        questionDiv.setAttribute('data-question', q.question);
        questionDiv.onclick = () => {
            messageInput.value = q.question;
            messageInput.focus();
            scrollToQuestion(q.question);
        };
        
        questionDiv.innerHTML = `
            <p class="text-sm line-clamp-2 mb-1 text-black">${escapeHtml(q.question)}</p>
            <p class="text-xs text-gray-500">${escapeHtml(q.timestamp || 'Vừa xong')}</p>
        `;
        questionsList.appendChild(questionDiv);
    });
}

function scrollToQuestion(questionText) {
    const userMessages = messages.filter(m => m.role === 'user');
    const targetMessage = userMessages.find(m => m.content === questionText);
    
    if (targetMessage) {
        const messageElement = document.querySelector(`[data-message-id="${targetMessage.id}"]`);
        if (messageElement) {
            messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            messageElement.classList.add('message-highlight');
            setTimeout(() => messageElement.classList.remove('message-highlight'), 2000);
        }
    }
}

// ========== API FUNCTIONS ==========
async function loadRecentQuestions() {
    try {
        const response = await fetch(`/api/get-questions/?conversation_id=${conversationId}`);
        const data = await response.json();
        if (data.success && data.questions) {
            questionHistory = data.questions;
            renderRecentQuestions();
        }
    } catch (error) {
        console.error('Lỗi khi tải câu hỏi:', error);
    }
}

async function loadExistingDocument() {
    if (initialDocuments && initialDocuments.length > 0) {
        const doc = initialDocuments[0];
        const fileExt = doc.name?.split('.').pop().toLowerCase() || 'pdf';
        const fileTypeDisplay = fileExt === 'docx' ? 'DOCX' : 'PDF';
        
        addMessage('assistant', `📄 Đang tải lại ${fileTypeDisplay} "${doc.name}"...`);
        
        try {
            const response = await fetch('/api/load-document/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ conversation_id: conversationId, document_id: doc.id })
            });
            const data = await response.json();
            
            if (data.success) {
                currentDocument = { name: doc.name, size: doc.size, uploadedAt: doc.uploaded_at };
                renderDocuments();
                addMessage('assistant', `✅ Đã tải lại ${fileTypeDisplay} "${doc.name}". Bạn có thể tiếp tục đặt câu hỏi.`);
            } else {
                addMessage('assistant', `⚠️ Không thể tải lại ${fileTypeDisplay}. Vui lòng tải lên lại file.`);
                currentDocument = null;
                renderDocuments();
            }
        } catch (error) {
            console.error('Lỗi tải lại document:', error);
            addMessage('assistant', `⚠️ Lỗi kết nối khi tải lại tài liệu. Vui lòng tải lên lại file.`);
            currentDocument = null;
            renderDocuments();
        }
    }
}

async function uploadFile(file) {
    const fileExt = file.name.split('.').pop().toLowerCase();
    if (fileExt !== 'pdf' && fileExt !== 'docx') {
        alert('Chỉ hỗ trợ file PDF hoặc DOCX');
        return;
    }
    
    if (currentDocument) {
        if (!confirm(`Bạn đã có tài liệu "${currentDocument.name}". Tải lên file mới sẽ thay thế tài liệu hiện tại. Bạn có muốn tiếp tục?`)) {
            return;
        }
    }
    
    const formData = new FormData();
    formData.append('pdf_file', file);
    formData.append('conversation_id', conversationId);
    
    const fileTypeDisplay = fileExt === 'docx' ? 'DOCX' : 'PDF';
    addMessage('assistant', `📄 Đang xử lý ${fileTypeDisplay} "${file.name}" (${formatFileSize(file.size)})...`);
    
    uploadBtn.disabled = true;
    uploadBtn.classList.add('opacity-50', 'cursor-not-allowed');
    
    try {
        const response = await fetch('/api/upload/', { method: 'POST', body: formData });
        const data = await response.json();
        
        if (data.success) {
            currentDocument = { name: data.filename, size: data.file_size || formatFileSize(file.size), uploadedAt: new Date().toLocaleString() };
            renderDocuments();
            addMessage('assistant', `✅ ${data.message}\n\nBạn có thể bắt đầu đặt câu hỏi về nội dung ${fileTypeDisplay} này.`);
        } else {
            addMessage('assistant', `❌ Lỗi: ${data.error || 'Không thể xử lý file. Vui lòng thử lại.'}`);
        }
    } catch (error) {
        console.error('Lỗi upload:', error);
        addMessage('assistant', `❌ Lỗi kết nối: ${error.message}`);
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    }
}

async function askQuestion(question) {
    if (!currentDocument) {
        addMessage('assistant', '⚠️ Vui lòng tải lên một file PDF hoặc DOCX trước khi đặt câu hỏi.');
        return;
    }
    
    if (isProcessing) {
        addMessage('assistant', '⏳ Vui lòng đợi câu hỏi trước được xử lý xong.');
        return;
    }
    
    isProcessing = true;
    sendBtn.disabled = true;
    sendBtn.classList.add('opacity-50', 'cursor-not-allowed');
    addMessage('user', question);
    
    const loadingId = Date.now().toString();
    messages.push({ id: loadingId, role: "assistant", content: "🤔 Đang suy nghĩ...", timestamp: getCurrentTimestamp() });
    renderMessages();
    
    try {
        const response = await fetch('/api/ask/', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question, conversation_id: conversationId })
        });
        const data = await response.json();
        messages = messages.filter(m => m.id !== loadingId);
        
        if (data.success) {
            let displayAnswer = data.answer;
            if (data.sources && data.sources.length > 0) {
                displayAnswer += '\n\n📚 **Nguồn tham khảo:**';
                data.sources.forEach((source, idx) => {
                    const pageInfo = source.page_number ? ` (Trang ${source.page_number})` : '';
                    const typeInfo = source.file_type ? ` [${source.file_type.toUpperCase()}]` : '';
                    displayAnswer += `\n${idx + 1}.${typeInfo}${pageInfo}: "${source.content.substring(0, 100)}..."`;
                });
            }
            addMessage('assistant', displayAnswer);
            await loadRecentQuestions();
        } else {
            addMessage('assistant', 'Có lỗi xảy ra khi xử lý câu hỏi. Vui lòng thử lại.');
        }
    } catch (error) {
        messages = messages.filter(m => m.id !== loadingId);
        console.error('Lỗi hỏi đáp:', error);
        addMessage('assistant', `❌ Lỗi kết nối: ${error.message}`);
    } finally {
        isProcessing = false;
        sendBtn.disabled = false;
        sendBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    }
}

async function clearHistory() {
    if (confirm('Bạn có chắc muốn xóa toàn bộ lịch sử trò chuyện?')) {
        try {
            const response = await fetch('/api/clear-history/', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ conversation_id: conversationId })
            });
            const data = await response.json();
            if (data.success) {
                messages = [{
                    id: "1", role: "assistant",
                    content: currentDocument ? "Lịch sử trò chuyện đã được xóa. Bạn có thể tiếp tục đặt câu hỏi về tài liệu hiện tại." : "Lịch sử trò chuyện đã được xóa. Vui lòng tải lên tài liệu để bắt đầu.",
                    timestamp: getCurrentTimestamp()
                }];
                renderMessages();
                await loadRecentQuestions();
            }
        } catch (error) {
            console.error('Lỗi xóa lịch sử:', error);
            addMessage('assistant', `❌ Lỗi kết nối: ${error.message}`);
        }
    }
}

async function clearDocument() {
    if (confirm('Bạn có chắc muốn xóa tài liệu đã tải lên? Bạn cần tải lên tài liệu mới để tiếp tục hỏi.')) {
        try {
            const response = await fetch('/api/clear-document/', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ conversation_id: conversationId })
            });
            const data = await response.json();
            if (data.success) {
                currentDocument = null;
                renderDocuments();
                messages = [{ id: "1", role: "assistant", content: "🗑️ Đã xóa tài liệu. Vui lòng tải lên tài liệu mới để tiếp tục.", timestamp: getCurrentTimestamp() }];
                renderMessages();
            }
        } catch (error) {
            console.error('Lỗi xóa tài liệu:', error);
            addMessage('assistant', `❌ Lỗi kết nối: ${error.message}`);
        }
    }
}

// ========== CHUNK CONFIG FUNCTIONS ==========
chunkSizeSlider?.addEventListener('input', () => chunkSizeValue.textContent = chunkSizeSlider.value);
chunkOverlapSlider?.addEventListener('input', () => chunkOverlapValue.textContent = chunkOverlapSlider.value);

async function loadChunkConfig() {
    try {
        const response = await fetch('/api/get-chunk-config/');
        const data = await response.json();
        if (data.success) {
            chunkSizeSlider.value = data.chunk_size;
            chunkOverlapSlider.value = data.chunk_overlap;
            chunkSizeValue.textContent = data.chunk_size;
            chunkOverlapValue.textContent = data.chunk_overlap;
        }
    } catch (error) {
        console.error('Lỗi tải cấu hình chunk:', error);
    }
}

async function applyChunkConfig() {
    const newChunkSize = parseInt(chunkSizeSlider.value);
    const newChunkOverlap = parseInt(chunkOverlapSlider.value);
    
    applyChunkBtn.disabled = true;
    applyChunkBtn.innerHTML = '<div class="spinner"></div> Đang xử lý...';
    chunkStatus.classList.remove('hidden');
    chunkStatus.textContent = '⏳ Đang xử lý lại tài liệu với cấu hình mới...';
    
    try {
        const response = await fetch('/api/update-chunk-config/', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chunk_size: newChunkSize, chunk_overlap: newChunkOverlap, conversation_id: conversationId })
        });
        const data = await response.json();
        
        if (data.success) {
            chunkStatus.textContent = '✅ ' + data.message;
            chunkStatus.classList.add('text-green-600');
            setTimeout(() => chunkStatus.classList.add('hidden'), 3000);
            if (currentDocument) {
                addMessage('assistant', `⚙️ Đã cập nhật cấu hình chunk: size=${newChunkSize}, overlap=${newChunkOverlap}. Tài liệu đã được xử lý lại.`);
            }
        } else {
            chunkStatus.textContent = '❌ Lỗi: ' + data.error;
        }
    } catch (error) {
        console.error('Lỗi áp dụng cấu hình:', error);
        chunkStatus.textContent = '❌ Lỗi kết nối: ' + error.message;
    } finally {
        applyChunkBtn.disabled = false;
        applyChunkBtn.innerHTML = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg> Áp dụng & Xử lý lại`;
        setTimeout(() => chunkStatus.classList.add('hidden'), 5000);
    }
}

async function resetChunkConfig() {
    chunkSizeSlider.value = 900;
    chunkOverlapSlider.value = 80;
    chunkSizeValue.textContent = 900;
    chunkOverlapValue.textContent = 80;
    await applyChunkConfig();
}

// ========== CHECK STATUS ==========
async function checkStatus() {
    if (initialDocuments && initialDocuments.length > 0) {
        await loadExistingDocument();
    } else {
        currentDocument = null;
        renderDocuments();
    }
    
    if (initialMessages && initialMessages.length > 0) {
        messages = initialMessages.map(msg => ({ id: msg.id, role: msg.role, content: msg.content, timestamp: msg.timestamp }));
        renderMessages();
    } else if (messages.length === 0 && !currentDocument) {
        addMessage('assistant', 'Xin chào! Tôi là trợ lý AI. Vui lòng tải lên một file PDF hoặc DOCX trước, sau đó bạn có thể đặt câu hỏi về nội dung của nó.');
    }
    await loadRecentQuestions();
}

// ========== EVENT LISTENERS ==========
chatForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const question = messageInput.value.trim();
    if (question && !isProcessing) {
        messageInput.value = '';
        await askQuestion(question);
    }
});

messageInput?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !isProcessing) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

uploadBtn?.addEventListener('click', () => !uploadBtn.disabled && fileInput.click());
fileInput?.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (file) {
        const fileExt = file.name.split('.').pop().toLowerCase();
        if (fileExt === 'pdf' || fileExt === 'docx') await uploadFile(file);
        else alert('Chỉ hỗ trợ file PDF hoặc DOCX');
    }
    fileInput.value = '';
});

clearHistoryBtn?.addEventListener('click', clearHistory);
clearDocumentBtn?.addEventListener('click', clearDocument);
refreshQuestionsBtn?.addEventListener('click', loadRecentQuestions);
applyChunkBtn?.addEventListener('click', applyChunkConfig);
resetChunkBtn?.addEventListener('click', resetChunkConfig);

// ========== INITIALIZE ==========
messageInput?.focus();
checkStatus();
loadChunkConfig();

window.setInputValue = (value) => { if (messageInput) { messageInput.value = value; messageInput.focus(); } };