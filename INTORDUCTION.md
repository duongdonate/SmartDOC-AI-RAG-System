

# DANH SÁCH TÍNH NĂNG TOÀN BỘ ỨNG DỤNG AI CHAT

##  **1. TRANG HOME**
- Giao diện giới thiệu ứng dụng AI Chat API
- **Kiểm tra tên người dùng từ database**: Tự động phát hiện và hiển thị form nhập tên hoặc nút "Vào trò chuyện ngay"
- Lưu tên vào database và localStorage
- Nút "Đổi tên người dùng" để cập nhật thông tin
- Hiển thị các tính năng nổi bật (Phản hồi tức thì, Câu trả lời chính xác, Bảo mật & Riêng tư)

## **2. TRANG DASHBOARD (Bảng điều khiển)**

### Quản lý hội thoại:
- **Hiển thị danh sách hội thoại**: Grid layout 2 cột, mỗi hội thoại hiển thị:
  - Tiêu đề hội thoại
  - Câu hỏi xem trước (preview)
  - Thời gian cập nhật cuối
  - Số lượng tin nhắn
- **Tạo hội thoại mới**: Nút "Trò chuyện mới" tạo conversation mới
- **Đổi tên hội thoại**: 
  - Icon bút chì xuất hiện khi hover
  - Modal popup nhập tên mới
  - Cập nhật UI ngay lập tức
- **Xóa hội thoại**:
  - Icon thùng rác xuất hiện khi hover
  - Modal xác nhận trước khi xóa
  - Xóa tất cả dữ liệu liên quan (messages, documents, files)
  - Animation fade-out khi xóa
- **Chuyển đến chat**: Click vào card hội thoại để mở

### Quản lý người dùng:
- Hiển thị tên người dùng từ database (API `/api/get-user/`)
- Tự động tạo user mặc định "User"
- Cập nhật tên người dùng qua API `/api/update-user-name/`

##  **3. TRANG CHAT**

### Quản lý tài liệu (Đa định dạng):
- **Upload tài liệu**: 
  - Hỗ trợ **PDF và DOCX**
  - Chỉ cho phép 1 tài liệu duy nhất mỗi hội thoại
  - Hiển thị thông báo khi đang xử lý
  - Thông báo thành công/thất bại
  - Tự động thay thế tài liệu cũ khi upload mới
  - **Tooltip cảnh báo** khi hover vào nút upload
- **Hiển thị tài liệu**: 
  - Card hiển thị tên file, kích thước, trạng thái
  - Màu xanh lá cho PDF, màu xanh dương cho DOCX
  - Icon khác biệt cho từng định dạng
- **Tự động tải lại tài liệu**: 
  - Khi vào lại chat, tự động load lại tài liệu đã upload
  - Khôi phục vector store để tiếp tục hỏi đáp
- **Xóa tài liệu**: 
  - Xóa file khỏi hệ thống
  - Xóa vector store
  - Reset trạng thái

### Cấu hình Chunk Strategy (Q4):
- **Tùy chỉnh Chunk Size**: 
  - Slider từ **600 → 1500** (tăng 100 mỗi mốc)
  - Mặc định: **900**
- **Tùy chỉnh Chunk Overlap**: 
  - Slider từ **50 → 150** (tăng 10 mỗi mốc)
  - Mặc định: **80**
- **Nút "Áp dụng & Xử lý lại"**: 
  - Tooltip cảnh báo khi hover
  - Xử lý lại toàn bộ tài liệu với cấu hình mới
  - Hiển thị trạng thái loading
- **Nút Reset**: Khôi phục cấu hình mặc định (900/80)

### Hỏi đáp thông minh (RAG):
- **Đặt câu hỏi**: 
  - Gửi câu hỏi về nội dung tài liệu (PDF/DOCX)
  - Hiển thị loading "Đang suy nghĩ..."
  - Ngăn gửi nhiều câu hỏi cùng lúc
- **Hiển thị câu trả lời**: 
  - Bubble chat với phân biệt user/assistant
  - Định dạng văn bản rõ ràng
  - **Hiển thị nguồn tham khảo kèm số trang** (Q5)
  - Định dạng: `[PDF] (Trang 5): "nội dung..."`
- **Lưu câu trả lời đầy đủ**: 
  - Lưu cả nội dung trả lời và nguồn tham khảo vào database
  - Khi reload trang, hiển thị đầy đủ nội dung đã lưu

### Lịch sử và quản lý:
- **Lưu lịch sử chat**: 
  - Tất cả tin nhắn được lưu vào database
  - Phân biệt user và assistant
  - Hiển thị timestamp
- **Recent Questions (Sidebar trái)**:
  - Hiển thị 15 câu hỏi gần nhất
  - Click vào câu hỏi để:
    - Tự động điền vào ô input
    - Cuộn đến vị trí câu hỏi trong chat
    - Highlight tin nhắn tương ứng
  - Nút refresh để tải lại danh sách
- **Documents (Sidebar phải)**:
  - Hiển thị thông tin tài liệu đã upload (kèm loại file)
  - Nút Upload tài liệu (hỗ trợ PDF/DOCX)
  - Nút Clear Document
  - Nút Clear History
  - **Note cảnh báo**: "Chỉ hỗ trợ 1 tài liệu duy nhất"

### Tương tác chat:
- **Gửi tin nhắn**:
  - Form input với nút Send
  - Gửi bằng phím Enter
  - Disable nút khi đang xử lý
- **Hiệu ứng UI**:
  - Animation slide-in cho tin nhắn mới
  - Highlight khi click vào recent question
  - Auto-scroll xuống tin nhắn mới nhất

## 🗄️ **4. HỆ THỐNG DATABASE (SQLite)**

### Models:
1. **User**: Lưu thông tin người dùng (name, created_at, updated_at)
2. **Conversation**: 
   - Lưu hội thoại (title, last_question, last_updated, total_messages, total_documents)
   - Liên kết với User
3. **Document**: 
   - Lưu thông tin file (file_name, file_path, file_size, uploaded_at)
   - Hỗ trợ cả PDF và DOCX
   - Liên kết với Conversation
4. **Message**: 
   - Lưu lịch sử tin nhắn (role, content, timestamp)
   - **Lưu cả nội dung trả lời và nguồn tham khảo**
   - Liên kết với Conversation
5. **QuestionHistory**: 
   - Lưu lịch sử câu hỏi cho sidebar
   - Liên kết với Conversation

### Lưu trữ file:
- Thư mục: `media/pdfs/{conversation_id}/`
- Hỗ trợ cả file .pdf và .docx
- Tự động xóa file khi xóa conversation

## 🤖 **5. HỆ THỐNG RAG (Retrieval-Augmented Generation)**

### Xử lý tài liệu:
- **Hỗ trợ đa định dạng**: 
  - PDF (PDFPlumberLoader)
  - DOCX (Docx2txtLoader)
- **Text Splitter**: 
  - Chunk size có thể tùy chỉnh (600-1500)
  - Chunk overlap có thể tùy chỉnh (50-150)
  - Mặc định: size=900, overlap=80
- **Embedding Model**: 
  - `all-MiniLM-L6-v2` (siêu nhẹ, tăng tốc độ)
  - Hỗ trợ đa ngôn ngữ
  - 384-dimensional embeddings
  - Batch size = 64 để xử lý song song
- **Vector Store**: FAISS để lưu trữ và tìm kiếm vector

### Xử lý câu hỏi:
- **Retriever**: Tìm kiếm top-2 chunks liên quan nhất (tối ưu tốc độ)
- **Số trang trong metadata**: Tự động thêm số trang cho PDF và số trang ảo cho DOCX
- **Prompt Template**: 
  - Yêu cầu trả lời 3-5 câu (100-150 từ)
  - Cho phép suy luận logic khi thiếu thông tin
  - Không cho phép nói "Tôi không biết"
- **LLM**: Qwen2.5:1.5b qua Ollama (localhost:11434)
- **Cache thông minh**: Tự động xóa cache sau 20 phút

## 🔧 **6. API ENDPOINTS**

### Page Views:
| Endpoint | Chức năng |
|----------|-----------|
| `/` | Trang home |
| `/dashboard/` | Dashboard |
| `/chat/` | Tạo chat mới |
| `/chat/<int:conversation_id>/` | Chat với hội thoại cụ thể |

### API Endpoints:
| Endpoint | Method | Chức năng |
|----------|--------|-----------|
| `/api/upload/` | POST | Upload tài liệu (PDF/DOCX) |
| `/api/ask/` | POST | Đặt câu hỏi |
| `/api/clear-history/` | POST | Xóa lịch sử chat |
| `/api/clear-document/` | POST | Xóa tài liệu |
| `/api/status/` | GET | Kiểm tra trạng thái |
| `/api/get-questions/` | GET | Lấy danh sách câu hỏi |
| `/api/get-conversations/` | GET | Lấy danh sách hội thoại |
| `/api/create-conversation/` | POST | Tạo hội thoại mới |
| `/api/get-user/` | GET | Lấy thông tin user |
| `/api/rename-conversation/` | POST | Đổi tên hội thoại |
| `/api/delete-conversation/` | POST | Xóa hội thoại |
| `/api/update-user-name/` | POST | Cập nhật tên user |
| `/api/load-document/` | POST | Tải lại document |
| `/api/get-chunk-config/` | GET | Lấy cấu hình chunk |
| `/api/update-chunk-config/` | POST | Cập nhật cấu hình chunk |

## 🎨 **7. GIAO DIỆN NGƯỜI DÙNG**

### Công nghệ:
- **TailwindCSS**: Styling responsive
- **SVG Icons**: Icon tùy chỉnh cho từng loại file
- **Custom CSS**: Animations, scrollbar, modal, tooltip

### Tính năng UI/UX:
- **Responsive design**: Hoạt động trên mọi thiết bị
- **Dark/Light mode**: Màu trắng đen chủ đạo
- **Modal popups**: Đổi tên, xác nhận xóa
- **Loading indicators**: Spinner khi xử lý
- **Tooltip warnings**: Cảnh báo khi hover vào nút nguy hiểm
- **Toast notifications**: Thông báo thành công/thất bại
- **Keyboard shortcuts**: 
  - Enter để gửi tin nhắn
  - ESC để đóng modal
- **Hover effects**: 
  - Hiển thị action buttons khi hover
  - Scale và shadow effects
  - Tooltip giải thích chức năng

## 🔒 **8. TÍNH NĂNG BẢO MẬT & TỐI ƯU**

- **Chạy local hoàn toàn**: Không gửi dữ liệu ra ngoài
- **Xử lý lỗi toàn diện**: 
  - File không hợp lệ (PDF/DOCX)
  - Lỗi kết nối Ollama
  - Conversation không tồn tại
- **Giới hạn tài nguyên**: 
  - Chỉ 1 tài liệu mỗi conversation
  - Giới hạn 150 chunks tối đa
  - Giới hạn 50 cache items
  - Giới hạn 20 câu hỏi hiển thị
- **Session management**: Lưu trạng thái qua database
- **Cache thông minh**: Tự động xóa cache cũ sau 20 phút

## 📦 **9. CÔNG NGHỆ SỬ DỤNG**

### Backend:
- Django 5.0.6
- LangChain 1.2.15
- FAISS (Vector database)
- Sentence Transformers (all-MiniLM-L6-v2)
- Ollama (Qwen2.5:1.5b)

### Frontend:
- HTML5 / TailwindCSS
- JavaScript (Vanilla, không framework)
- SVG Icons

### Database:
- SQLite3

### Xử lý tài liệu:
- PDFPlumber (PDF)
- Docx2txtLoader (DOCX)
- python-docx

## 🚀 **10. TÍNH NĂNG ĐẶC BIỆT**

1. **Đa định dạng tài liệu**: Hỗ trợ cả PDF và DOCX
2. **Hiển thị số trang trong citation**: Nguồn tham khảo kèm số trang cụ thể
3. **Tùy chỉnh Chunk Strategy**: Người dùng có thể điều chỉnh chunk_size và chunk_overlap
4. **Persistent storage**: Lưu tất cả dữ liệu vào database
5. **Session recovery**: Tự động khôi phục trạng thái khi reload
6. **Real-time UI updates**: Cập nhật giao diện không cần refresh
7. **Error recovery**: Tự động thử lại khi có lỗi kết nối
8. **Resource cleanup**: Tự động xóa file khi xóa conversation
9. **Tooltip warnings**: Cảnh báo trước các hành động quan trọng
10. **Cache thông minh**: Tăng tốc độ trả lời cho câu hỏi lặp lại

---

## 📊 **THỐNG KÊ TÍNH NĂNG**

| Loại tính năng | Số lượng |
|---------------|----------|
| Trang giao diện | 3 |
| Model database | 5 |
| API endpoints | 15 |
| Chức năng chat | 15 |
| Quản lý hội thoại | 6 |
| Xử lý tài liệu | 8 |
| Tương tác UI | 20+ |
| **Tổng số tính năng** | **72+** |

---

## 📋 **CÁC TÍNH NĂNG MỚI ĐÃ BỔ SUNG**

| STT | Tính năng | Mô tả |
|-----|-----------|-------|
| 1 | **Hỗ trợ file DOCX** | Upload và xử lý file Word |
| 2 | **Hiển thị số trang** | Citation kèm số trang cụ thể |
| 3 | **Chunk Strategy UI** | Slider tùy chỉnh chunk_size (600-1500) và chunk_overlap (50-150) |
| 4 | **Tooltip cảnh báo** | Hiển thị giải thích khi hover vào nút nguy hiểm |
| 5 | **Lưu full answer** | Lưu cả nội dung trả lời và nguồn tham khảo |
| 6 | **Phân biệt màu sắc** | Xanh lá cho PDF, xanh dương cho DOCX |
| 7 | **Cache thông minh** | Tự động xóa cache sau 20 phút |
| 8 | **Reset chunk config** | Khôi phục cấu hình mặc định (900/80) |