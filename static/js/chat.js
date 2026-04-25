// ========== DOM ELEMENTS ==========
const messageInput = document.getElementById("messageInput");
const chatForm = document.getElementById("chatForm");
const messagesContainer = document.getElementById("messagesContainer");
const uploadBtn = document.getElementById("uploadBtn");
const fileInput = document.getElementById("fileInput");
const clearHistoryBtn = document.getElementById("clearHistoryBtn");
const clearDocumentBtn = document.getElementById("clearDocumentBtn");
const documentsList = document.getElementById("documentsList");
const noDocumentsMsg = document.getElementById("noDocumentsMsg");
const questionsList = document.getElementById("questionsList");
const refreshQuestionsBtn = document.getElementById("refreshQuestionsBtn");
const sendBtn = document.getElementById("sendBtn");
const chunkSizeSlider = document.getElementById("chunkSizeSlider");
const chunkOverlapSlider = document.getElementById("chunkOverlapSlider");
const chunkSizeValue = document.getElementById("chunkSizeValue");
const chunkOverlapValue = document.getElementById("chunkOverlapValue");
const applyChunkBtn = document.getElementById("applyChunkBtn");
const resetChunkBtn = document.getElementById("resetChunkBtn");
const chunkStatus = document.getElementById("chunkStatus");

// ========== STATE ==========
let messages = [];
let currentDocuments = [];
let questionHistory = [];
let isProcessing = false;
let loadingMessageId = null; // Lưu ID của message loading

// ========== HELPER FUNCTIONS ==========
const md = window.markdownit({
  html: true,
  linkify: true,
  typographer: true,
});

if (window.texmath) {
  md.use(window.texmath, {
    engine: katex,
    delimiters: "dollars", // hỗ trợ $...$ và $$...$$
  });
}

function renderMarkdown(text) {
  return md.render(text);
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function getCurrentTimestamp() {
  return new Intl.DateTimeFormat("vi-VN", {
    timeZone: "Asia/Ho_Chi_Minh",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date());
}

function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

// ========== LOADING INDICATOR FUNCTIONS ==========
function addTypingIndicator() {
  loadingMessageId = Date.now().toString();
  const typingMessage = {
    id: loadingMessageId,
    role: "assistant",
    content: "",
    isTyping: true,
    timestamp: getCurrentTimestamp(),
  };
  messages.push(typingMessage);
  renderMessages();
  return loadingMessageId;
}

function removeTypingIndicator() {
  if (loadingMessageId) {
    messages = messages.filter((m) => m.id !== loadingMessageId);
    loadingMessageId = null;
    renderMessages();
  }
}

// ========== RENDER FUNCTIONS ==========
function renderMessages() {
  if (!messagesContainer) return;

  messagesContainer.innerHTML = "";
  messages.forEach((message, index) => {
    const messageDiv = document.createElement("div");
    messageDiv.className = `flex ${message.role === "user" ? "justify-end" : "justify-start"} message-animation`;
    messageDiv.setAttribute("data-message-id", message.id);
    messageDiv.setAttribute("data-message-index", index);

    // Kiểm tra nếu là typing indicator
    if (message.isTyping) {
      const bubbleDiv = document.createElement("div");
      bubbleDiv.className = "text-black rounded-2xl px-5 py-3";
      bubbleDiv.innerHTML = `
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                <div class="text-xs mt-2 text-gray-400">${escapeHtml(message.timestamp)}</div>
            `;
      messageDiv.appendChild(bubbleDiv);
    } else {
      const bubbleDiv = document.createElement("div");
      bubbleDiv.className = `${
        message.role === "user"
          ? "max-w-2xl bg-black text-white"
          : "w-full text-black"
      } rounded-2xl px-5 py-3`;

      bubbleDiv.innerHTML = `
                <div class="font-sm markdown-body">${renderMarkdown(message.content)}</div>
                <p class="text-xs mt-2 ${message.role === "user" ? "text-gray-300" : "text-black"}">
                    ${escapeHtml(message.timestamp)}
                </p>
            `;
      messageDiv.appendChild(bubbleDiv);
    }

    messagesContainer.appendChild(messageDiv);
  });

  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addMessage(role, content, messageId = null) {
  const newMessage = {
    id: messageId || Date.now().toString(),
    role: role,
    content: content,
    timestamp: getCurrentTimestamp(),
  };
  messages.push(newMessage);
  renderMessages();
  return newMessage.id;
}

function renderDocuments() {
  if (!documentsList) return;

  // Sử dụng biến mảng currentDocuments thay vì currentDocument đơn lẻ
  if (currentDocuments && currentDocuments.length > 0) {
    if (noDocumentsMsg) noDocumentsMsg.style.display = "none";

    // Lặp qua từng file để vẽ UI
    currentDocuments.forEach((doc) => {
      const fileExt = doc.name?.split(".").pop().toLowerCase() || "pdf";
      const isDocx = fileExt === "docx";
      const bgColor = isDocx ? "bg-blue-600" : "bg-green-600";
      const borderColor = isDocx ? "border-blue-500" : "border-green-500";
      const bgLight = isDocx ? "bg-blue-50" : "bg-green-50";
      const fileTypeDisplay = isDocx ? "DOCX" : "PDF";

      const fileIcon = isDocx
        ? `<svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>`
        : `<svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path></svg>`;

      // Dùng += để thêm (append) từng thẻ div vào danh sách.
      // Tui thêm margin-bottom (mb-3) để các tài liệu cách nhau ra cho đẹp.
      // Tui cũng thêm thuộc tính title vào tên file để user hover chuột có thể đọc được tên đầy đủ nếu bị truncate
      documentsList.innerHTML += `
        <div class="p-4 mb-3 rounded-lg border ${borderColor} ${bgLight} document-animation">
            <div class="flex items-start gap-3">
                <div class="w-10 h-10 rounded-lg ${bgColor} flex items-center justify-center flex-shrink-0">
                    ${fileIcon}
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium truncate mb-1 text-gray-900" title="${escapeHtml(doc.name)}">${escapeHtml(doc.name)}</p>
                    <div class="flex items-center justify-between text-xs text-gray-600">
                        <span>${fileTypeDisplay}</span>
                        <span>${escapeHtml(doc.size)}</span>
                    </div>
                    <div class="mt-2 text-xs ${isDocx ? "text-blue-600" : "text-green-600"}">✓ Đã sẵn sàng</div>
                </div>
            </div>
        </div>
      `;
    });
  } else {
    if (noDocumentsMsg) noDocumentsMsg.style.display = "block";
    documentsList.innerHTML = "";
    if (noDocumentsMsg) documentsList.appendChild(noDocumentsMsg);
  }
}

function renderRecentQuestions() {
  if (!questionsList) return;

  if (questionHistory.length === 0) {
    questionsList.innerHTML = `<div class="text-center text-gray-500 text-sm py-8">Chưa có câu hỏi nào</div>`;
    return;
  }

  questionsList.innerHTML = "";
  const recentQuestions = [...questionHistory].reverse().slice(0, 15);

  recentQuestions.forEach((q, idx) => {
    const questionDiv = document.createElement("div");
    questionDiv.className =
      "question-item p-3 rounded-lg border border-black hover:bg-gray-100 cursor-pointer transition-colors";
    questionDiv.setAttribute("data-question", q.question);
    questionDiv.onclick = () => {
      messageInput.value = q.question;
      messageInput.focus();
      scrollToQuestion(q.question);
    };

    questionDiv.innerHTML = `
            <p class="text-sm line-clamp-2 mb-1 text-black">${escapeHtml(q.question)}</p>
            <p class="text-xs text-gray-500">${escapeHtml(q.timestamp || "Vừa xong")}</p>
        `;
    questionsList.appendChild(questionDiv);
  });
}

function scrollToQuestion(questionText) {
  const userMessages = messages.filter((m) => m.role === "user");
  const targetMessage = userMessages.find((m) => m.content === questionText);

  if (targetMessage) {
    const messageElement = document.querySelector(
      `[data-message-id="${targetMessage.id}"]`,
    );
    if (messageElement) {
      messageElement.scrollIntoView({ behavior: "smooth", block: "center" });
      messageElement.classList.add("message-highlight");
      setTimeout(
        () => messageElement.classList.remove("message-highlight"),
        2000,
      );
    }
  }
}

// ========== API FUNCTIONS ==========
async function loadRecentQuestions() {
  try {
    const response = await fetch(
      `/api/get-questions/?conversation_id=${conversationId}`,
    );
    const data = await response.json();
    if (data.success && data.questions) {
      questionHistory = data.questions;
      renderRecentQuestions();
    }
  } catch (error) {
    console.error("Lỗi khi tải câu hỏi:", error);
  }
}

// Đổi tên hàm thành số nhiều cho chuẩn nhé, nhớ cập nhật chỗ gọi hàm này (ví dụ trong window.onload)
async function loadExistingDocument() {
  if (initialDocuments && initialDocuments.length > 0) {
    const fileCount = initialDocuments.length;

    addMessage(
      "assistant",
      `📄 Đang tải lại ${fileCount} tài liệu vào bộ nhớ...`,
    );

    try {
      const response = await fetch("/api/load-document/", {
        // Đảm bảo URL khớp với urls.py của bạn
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: conversationId,
          // Không cần gửi document_id nữa vì backend đã quét toàn bộ theo conversation_id
        }),
      });
      const data = await response.json();

      if (data.success) {
        // Gán toàn bộ danh sách file vào biến mảng hiện tại
        currentDocuments = initialDocuments.map((doc) => ({
          name: doc.name,
          size: doc.size, // Nhớ format dung lượng nếu backend chưa format
          uploadedAt: doc.uploaded_at || new Date().toLocaleString(),
        }));

        renderDocuments();

        addMessage(
          "assistant",
          `✅ Đã tải lại thành công ${fileCount} tài liệu. Bạn có thể tiếp tục đặt câu hỏi.`,
        );
      } else {
        addMessage(
          "assistant",
          `⚠️ Không thể tải lại tài liệu. Lỗi: ${data.error || "Vui lòng tải lên lại file."}`,
        );
        currentDocuments = []; // Đặt lại thành mảng rỗng
        renderDocuments();
      }
    } catch (error) {
      console.error("Lỗi tải lại documents:", error);
      addMessage(
        "assistant",
        `⚠️ Lỗi kết nối khi tải lại tài liệu. Vui lòng tải lên lại file.`,
      );
      currentDocuments = []; // Đặt lại thành mảng rỗng
      renderDocuments();
    }
  }
}

async function askQuestion(question) {
  if (!currentDocuments || currentDocuments.length === 0) {
    addMessage(
      "assistant",
      "⚠️ Vui lòng tải lên một file PDF hoặc DOCX trước khi đặt câu hỏi.",
    );
    return;
  }

  if (isProcessing) {
    addMessage("assistant", "⏳ Vui lòng đợi câu hỏi trước được xử lý xong.");
    return;
  }

  isProcessing = true;
  sendBtn.disabled = true;
  sendBtn.classList.add("opacity-50", "cursor-not-allowed");

  // Thêm câu hỏi của user
  addMessage("user", question);

  // Thêm typing indicator thay vì dòng chữ "Đang suy nghĩ..."
  addTypingIndicator();

  try {
    const response = await fetch("/api/ask/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: question,
        conversation_id: conversationId,
      }),
    });

    const data = await response.json();

    // Xóa typing indicator
    removeTypingIndicator();

    if (data.success) {
      let displayAnswer = data.full_answer;
      addMessage("assistant", displayAnswer);
      await loadRecentQuestions();
    } else {
      addMessage(
        "assistant",
        "Có lỗi xảy ra khi xử lý câu hỏi. Vui lòng thử lại.",
      );
    }
  } catch (error) {
    removeTypingIndicator();
    console.error("Lỗi hỏi đáp:", error);
    addMessage("assistant", `❌ Lỗi kết nối: ${error.message}`);
  } finally {
    isProcessing = false;
    sendBtn.disabled = false;
    sendBtn.classList.remove("opacity-50", "cursor-not-allowed");
  }
}

async function clearHistory() {
  if (confirm("Bạn có chắc muốn xóa toàn bộ lịch sử trò chuyện?")) {
    try {
      const response = await fetch("/api/clear-history/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ conversation_id: conversationId }),
      });
      const data = await response.json();
      if (data.success) {
        messages = [
          {
            id: "1",
            role: "assistant",
            content:
              currentDocuments && currentDocuments.length > 0
                ? "Lịch sử trò chuyện đã được xóa. Bạn có thể tiếp tục đặt câu hỏi về tài liệu hiện tại."
                : "Lịch sử trò chuyện đã được xóa. Vui lòng tải lên tài liệu để bắt đầu.",
            timestamp: getCurrentTimestamp(),
          },
        ];
        renderMessages();
        await loadRecentQuestions();
      }
    } catch (error) {
      console.error("Lỗi xóa lịch sử:", error);
      addMessage("assistant", `❌ Lỗi kết nối: ${error.message}`);
    }
  }
}

async function clearDocument() {
  if (
    confirm(
      "Bạn có chắc muốn xóa tài liệu đã tải lên? Bạn cần tải lên tài liệu mới để tiếp tục hỏi.",
    )
  ) {
    try {
      const response = await fetch("/api/clear-document/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ conversation_id: conversationId }),
      });
      const data = await response.json();
      if (data.success) {
        currentDocuments = [];
        renderDocuments();
        messages = [
          {
            id: "1",
            role: "assistant",
            content:
              "🗑️ Đã xóa tài liệu. Vui lòng tải lên tài liệu mới để tiếp tục.",
            timestamp: getCurrentTimestamp(),
          },
        ];
        renderMessages();
      }
    } catch (error) {
      console.error("Lỗi xóa tài liệu:", error);
      addMessage("assistant", `❌ Lỗi kết nối: ${error.message}`);
    }
  }
}

// ========== CHUNK CONFIG FUNCTIONS ==========
chunkSizeSlider?.addEventListener(
  "input",
  () => (chunkSizeValue.textContent = chunkSizeSlider.value),
);
chunkOverlapSlider?.addEventListener(
  "input",
  () => (chunkOverlapValue.textContent = chunkOverlapSlider.value),
);

async function loadChunkConfig() {
  try {
    const response = await fetch("/api/get-chunk-config/");
    const data = await response.json();
    if (data.success) {
      chunkSizeSlider.value = data.chunk_size;
      chunkOverlapSlider.value = data.chunk_overlap;
      chunkSizeValue.textContent = data.chunk_size;
      chunkOverlapValue.textContent = data.chunk_overlap;
    }
  } catch (error) {
    console.error("Lỗi tải cấu hình chunk:", error);
  }
}

async function applyChunkConfig() {
  const newChunkSize = parseInt(chunkSizeSlider.value);
  const newChunkOverlap = parseInt(chunkOverlapSlider.value);

  applyChunkBtn.disabled = true;
  applyChunkBtn.innerHTML = '<div class="spinner"></div> Đang xử lý...';
  chunkStatus.classList.remove("hidden");
  chunkStatus.textContent = "⏳ Đang xử lý lại tài liệu với cấu hình mới...";

  try {
    const response = await fetch("/api/update-chunk-config/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chunk_size: newChunkSize,
        chunk_overlap: newChunkOverlap,
        conversation_id: conversationId,
      }),
    });
    const data = await response.json();

    if (data.success) {
      chunkStatus.textContent = "✅ " + data.message;
      chunkStatus.classList.add("text-green-600");
      setTimeout(() => chunkStatus.classList.add("hidden"), 3000);
      if (currentDocuments && currentDocuments.length > 0) {
        addMessage(
          "assistant",
          `⚙️ Đã cập nhật cấu hình chunk: size=${newChunkSize}, overlap=${newChunkOverlap}. Tài liệu đã được xử lý lại.`,
        );
      }
    } else {
      chunkStatus.textContent = "❌ Lỗi: " + data.error;
    }
  } catch (error) {
    console.error("Lỗi áp dụng cấu hình:", error);
    chunkStatus.textContent = "❌ Lỗi kết nối: " + error.message;
  } finally {
    applyChunkBtn.disabled = false;
    applyChunkBtn.innerHTML = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg> Áp dụng & Xử lý lại`;
    setTimeout(() => chunkStatus.classList.add("hidden"), 5000);
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
  console.log("Initial documents from backend:", initialDocuments);
  if (initialDocuments && initialDocuments.length > 0) {
    await loadExistingDocument();
  } else {
    currentDocuments = [];
    renderDocuments();
  }

  console.log("Initial messages from backend:", initialMessages);
  if (initialMessages && initialMessages.length > 0) {
    messages = initialMessages.map((msg) => ({
      id: msg.id,
      role: msg.role,
      content: msg.content,
      timestamp: msg.timestamp,
    }));
    renderMessages();
  } else if (
    messages.length === 0 &&
    !currentDocuments &&
    !currentDocuments.length > 0
  ) {
    addMessage(
      "assistant",
      "Xin chào! Tôi là trợ lý AI. Vui lòng tải lên một file PDF hoặc DOCX trước, sau đó bạn có thể đặt câu hỏi về nội dung của nó.",
    );
  }
  await loadRecentQuestions();
}

// ========== EVENT LISTENERS ==========
chatForm?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = messageInput.value.trim();
  if (question && !isProcessing) {
    messageInput.value = "";
    await askQuestion(question);
  }
});

messageInput?.addEventListener("keypress", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !isProcessing) {
    e.preventDefault();
    chatForm.dispatchEvent(new Event("submit"));
  }
});

uploadBtn?.addEventListener(
  "click",
  () => !uploadBtn.disabled && fileInput.click(),
);
fileInput?.addEventListener("change", async (e) => {
  // Chuyển e.target.files (FileList) thành một Array chuẩn để dễ thao tác
  const files = Array.from(e.target.files);

  if (files.length > 0) {
    const validFiles = [];
    const invalidFiles = [];

    // Kiểm tra đuôi file cho TẤT CẢ các file được chọn
    files.forEach((file) => {
      const fileExt = file.name.split(".").pop().toLowerCase();
      if (fileExt === "pdf" || fileExt === "docx") {
        validFiles.push(file);
      } else {
        invalidFiles.push(file.name);
      }
    });

    // Nếu có file sai định dạng, cảnh báo cho user
    if (invalidFiles.length > 0) {
      alert(
        `⚠️ Các file sau không hợp lệ (chỉ hỗ trợ PDF, DOCX):\n${invalidFiles.join(", ")}`,
      );
    }

    // Tiến hành upload những file hợp lệ
    if (validFiles.length > 0) {
      // Đổi tên hàm thành uploadFiles (số nhiều) cho chuẩn ý nghĩa nhé
      await uploadFiles(validFiles);
    }
  }

  // Reset input để user có thể chọn lại đúng file đó nếu muốn
  fileInput.value = "";
});

async function uploadFiles(filesArray) {
  if (!filesArray || filesArray.length === 0) return;

  // 1. Kiểm tra ghi đè tài liệu cũ
  // Tui khuyên bạn nên đổi biến toàn cục `currentDocument` thành `currentDocuments` (dạng mảng [])
  // Nhưng tui viết code dự phòng ở đây để lỡ bạn chưa đổi thì nó vẫn chạy được.

  // 2. Chuẩn bị FormData (quan trọng nhất)
  const formData = new FormData();
  let totalSize = 0;

  // Lặp qua mảng file để append vào cùng 1 key 'files'
  filesArray.forEach((file) => {
    formData.append("files", file);
    totalSize += file.size;
  });
  formData.append("conversation_id", conversationId);

  // 3. Hiển thị UI đang xử lý
  addMessage(
    "assistant",
    `📄 Đang xử lý ${filesArray.length} tài liệu (Tổng dung lượng: ${formatFileSize(totalSize)})...`,
  );

  uploadBtn.disabled = true;
  uploadBtn.classList.add("opacity-50", "cursor-not-allowed");

  try {
    // Lưu ý: Đảm bảo URL này khớp với URL bạn định nghĩa trong file urls.py của Django
    const response = await fetch("/api/upload/", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();

    if (data.success) {
      // 4. Cập nhật lại State hiển thị
      // Nếu bạn đã đổi thành mảng currentDocuments
      if (typeof currentDocuments !== "undefined") {
        currentDocuments = filesArray.map((f) => ({
          name: f.name,
          size: formatFileSize(f.size),
          uploadedAt: new Date().toLocaleString(),
        }));
      } else {
        // Fallback: nếu bạn vẫn giữ biến currentDocument (1 object)
        currentDocuments = {
          name: data.file_names
            ? data.file_names.join(", ")
            : `${filesArray.length} tài liệu`,
          size: data.total_size || formatFileSize(totalSize),
          uploadedAt: new Date().toLocaleString(),
        };
      }

      // Cập nhật giao diện danh sách file bên Sidebar
      if (typeof renderDocuments === "function") renderDocuments();

      addMessage(
        "assistant",
        `✅ ${data.message}\n\nBạn có thể bắt đầu đặt câu hỏi về nội dung các tài liệu này.`,
      );
    } else {
      addMessage(
        "assistant",
        `❌ Lỗi: ${data.error || "Không thể xử lý file. Vui lòng thử lại."}`,
      );
    }
  } catch (error) {
    console.error("Lỗi upload:", error);
    addMessage("assistant", `❌ Lỗi kết nối: ${error.message}`);
  } finally {
    // 5. Mở khóa nút upload
    uploadBtn.disabled = false;
    uploadBtn.classList.remove("opacity-50", "cursor-not-allowed");
  }
}

clearHistoryBtn?.addEventListener("click", clearHistory);
clearDocumentBtn?.addEventListener("click", clearDocument);
refreshQuestionsBtn?.addEventListener("click", loadRecentQuestions);
applyChunkBtn?.addEventListener("click", applyChunkConfig);
resetChunkBtn?.addEventListener("click", resetChunkConfig);

// ========== INITIALIZE ==========
messageInput?.focus();
checkStatus();
loadChunkConfig();

window.setInputValue = (value) => {
  if (messageInput) {
    messageInput.value = value;
    messageInput.focus();
  }
};
