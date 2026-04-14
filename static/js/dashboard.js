// ========== DOM ELEMENTS ==========
const renameModal = document.getElementById('renameModal');
const newConversationName = document.getElementById('newConversationName');
const cancelRenameBtn = document.getElementById('cancelRenameBtn');
const confirmRenameBtn = document.getElementById('confirmRenameBtn');
const renameSpinner = document.getElementById('renameSpinner');

const deleteModal = document.getElementById('deleteModal');
const deleteConversationTitle = document.getElementById('deleteConversationTitle');
const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
const deleteSpinner = document.getElementById('deleteSpinner');

// ========== STATE ==========
let currentRenameId = null;
let currentDeleteId = null;
let currentDeleteTitle = null;

// ========== MODAL ĐỔI TÊN ==========
window.openRenameModal = function(conversationId, currentTitle) {
    console.log('openRenameModal called:', conversationId, currentTitle);
    currentRenameId = conversationId;
    newConversationName.value = currentTitle;
    renameModal.classList.add('active');
    setTimeout(() => {
        newConversationName.focus();
        newConversationName.select();
    }, 100);
};

function closeRenameModal() {
    renameModal.classList.remove('active');
    currentRenameId = null;
    newConversationName.value = '';
}

async function confirmRename() {
    const newName = newConversationName.value.trim();
    
    if (!newName) {
        alert('Vui lòng nhập tên hội thoại');
        return;
    }
    
    if (!currentRenameId) return;
    
    renameSpinner.classList.remove('hidden');
    confirmRenameBtn.disabled = true;
    
    try {
        const response = await fetch('/api/rename-conversation/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                conversation_id: currentRenameId,
                new_title: newName
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const titleElement = document.querySelector(`.conversation-title-${currentRenameId}`);
            if (titleElement) {
                titleElement.textContent = newName;
            }
            closeRenameModal();
            console.log('Đổi tên thành công');
        } else {
            alert(data.error || 'Có lỗi xảy ra khi đổi tên');
        }
    } catch (error) {
        console.error('Lỗi khi đổi tên:', error);
        alert('Lỗi kết nối: ' + error.message);
    } finally {
        renameSpinner.classList.add('hidden');
        confirmRenameBtn.disabled = false;
    }
}

// ========== MODAL XÓA HỘI THOẠI ==========
window.openDeleteModal = function(conversationId, conversationTitle) {
    console.log('openDeleteModal called:', conversationId, conversationTitle);
    currentDeleteId = conversationId;
    currentDeleteTitle = conversationTitle;
    deleteConversationTitle.textContent = conversationTitle;
    deleteModal.classList.add('active');
};

function closeDeleteModal() {
    deleteModal.classList.remove('active');
    currentDeleteId = null;
    currentDeleteTitle = null;
}

async function confirmDelete() {
    if (!currentDeleteId) return;
    
    deleteSpinner.classList.remove('hidden');
    confirmDeleteBtn.disabled = true;
    
    try {
        const response = await fetch('/api/delete-conversation/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ conversation_id: currentDeleteId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const chatItem = document.querySelector(`.chat-item[data-chat-id="${currentDeleteId}"]`);
            if (chatItem) {
                chatItem.classList.add('fade-out');
                setTimeout(() => {
                    chatItem.remove();
                    const remainingItems = document.querySelectorAll('.chat-item');
                    if (remainingItems.length === 0) {
                        location.reload();
                    }
                }, 300);
            }
            closeDeleteModal();
            console.log('Xóa hội thoại thành công');
        } else {
            alert(data.error || 'Có lỗi xảy ra khi xóa hội thoại');
        }
    } catch (error) {
        console.error('Lỗi khi xóa:', error);
        alert('Lỗi kết nối: ' + error.message);
    } finally {
        deleteSpinner.classList.add('hidden');
        confirmDeleteBtn.disabled = false;
    }
}

// ========== LẤY TÊN NGƯỜI DÙNG ==========
async function loadUserFromDatabase() {
    try {
        const response = await fetch('/api/get-user/');
        const data = await response.json();
        if (data.success && data.user_name) {
            const welcomeMessage = document.getElementById("welcomeMessage");
            if (welcomeMessage) {
                welcomeMessage.textContent = `Chào mừng quay trở lại, ${data.user_name}`;
            }
            localStorage.setItem("userName", data.user_name);
        } else {
            const userName = localStorage.getItem("userName") || "Người dùng";
            const welcomeMessage = document.getElementById("welcomeMessage");
            if (welcomeMessage) {
                welcomeMessage.textContent = `Chào mừng quay trở lại, ${userName}`;
            }
        }
    } catch (error) {
        console.error('Lỗi khi lấy tên người dùng:', error);
        const userName = localStorage.getItem("userName") || "Người dùng";
        const welcomeMessage = document.getElementById("welcomeMessage");
        if (welcomeMessage) {
            welcomeMessage.textContent = `Chào mừng quay trở lại, ${userName}`;
        }
    }
}

// ========== GẮN SỰ KIỆN ==========
function bindButtons() {
    const editButtons = document.querySelectorAll('.edit-btn');
    console.log('Found edit buttons:', editButtons.length);
    editButtons.forEach(btn => {
        btn.removeEventListener('click', handleEditClick);
        btn.addEventListener('click', handleEditClick);
    });
    
    const deleteButtons = document.querySelectorAll('.delete-btn');
    console.log('Found delete buttons:', deleteButtons.length);
    deleteButtons.forEach(btn => {
        btn.removeEventListener('click', handleDeleteClick);
        btn.addEventListener('click', handleDeleteClick);
    });
}

function handleEditClick(event) {
    event.stopPropagation();
    const chatId = this.getAttribute('data-chat-id');
    const chatTitle = this.getAttribute('data-chat-title');
    console.log('Edit button clicked:', chatId, chatTitle);
    window.openRenameModal(chatId, chatTitle);
}

function handleDeleteClick(event) {
    event.stopPropagation();
    const chatId = this.getAttribute('data-chat-id');
    const chatTitle = this.getAttribute('data-chat-title');
    console.log('Delete button clicked:', chatId, chatTitle);
    window.openDeleteModal(chatId, chatTitle);
}

function bindChatItems() {
    const chatItems = document.querySelectorAll('.chat-item');
    chatItems.forEach(item => {
        item.removeEventListener('click', handleChatClick);
        item.addEventListener('click', handleChatClick);
    });
}

function handleChatClick(e) {
    if (e.target.closest('.edit-btn') || e.target.closest('.delete-btn')) {
        return;
    }
    const chatId = this.getAttribute('data-chat-id');
    window.location.href = `/chat/${chatId}`;
}

// ========== EVENT LISTENERS CHO MODAL ==========
renameModal.addEventListener('click', (e) => {
    if (e.target === renameModal) closeRenameModal();
});
cancelRenameBtn.addEventListener('click', closeRenameModal);
confirmRenameBtn.addEventListener('click', confirmRename);
newConversationName.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') confirmRename();
});

deleteModal.addEventListener('click', (e) => {
    if (e.target === deleteModal) closeDeleteModal();
});
cancelDeleteBtn.addEventListener('click', closeDeleteModal);
confirmDeleteBtn.addEventListener('click', confirmDelete);

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        if (renameModal.classList.contains('active')) closeRenameModal();
        if (deleteModal.classList.contains('active')) closeDeleteModal();
    }
});

// ========== KHỞI TẠO ==========
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing...');
    console.log('Chat history data:', chatHistoryData);
    
    loadUserFromDatabase();
    bindButtons();
    bindChatItems();
});