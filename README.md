# SmartDoc AI V2 - Hướng dẫn cài đặt và sử dụng

## Giới thiệu

SmartDoc AI V2 là một ứng dụng trò chuyện thông minh cho phép người dùng tải lên đa dạng tài liệu (PDF, DOCX) và đặt câu hỏi về nội dung của chúng.

Hệ thống áp dụng công nghệ Hybrid Search (kết hợp Semantic Search và Keyword Search) cùng mô hình Cross-Encoder Re-ranking, mang lại độ chính xác cao trong việc trích xuất thông tin. Mọi dữ liệu được xử lý cục bộ qua Ollama (Qwen2.5:7b), đảm bảo bảo mật và riêng tư 100%.

## Tính năng nổi bật

- Hỗ trợ đa định dạng: Xử lý mượt mà cả file PDF (sử dụng thư viện pdfplumber cho độ chính xác cao) và file DOCX.
- Tải lên cộng dồn (Incremental Upload): Hỗ trợ tải lên nhiều file cùng lúc và tải thêm file mới vào phiên làm việc hiện tại mà không làm mất hoặc ghi đè dữ liệu của các file cũ.
- Lưu trữ Vector cứng (Persistent Vector Storage): Hệ thống tự động lưu trữ cơ sở dữ liệu vector (FAISS Index) xuống ổ cứng. Khi truy cập lại các đoạn chat cũ, hệ thống sẽ nạp trực tiếp từ ổ cứng lên RAM mà không cần phải phân tích và băm lại tài liệu từ đầu, giúp tối ưu hiệu năng và tiết kiệm thời gian.
- Tìm kiếm lai (Hybrid Search): Khắc phục điểm yếu của Vector thuần túy bằng cách kết hợp Vector Search (FAISS) và Keyword Search (BM25Okapi). Đảm bảo tìm kiếm chính xác các mã số, tên riêng và từ khóa đặc thù.
- Chấm điểm và sắp xếp ứng viên (Re-ranking): Tích hợp mô hình Cross-Encoder để chấm điểm và sắp xếp lại các đoạn văn bản ứng viên, cung cấp ngữ cảnh chuẩn xác nhất cho LLM.
- Trích dẫn nguồn minh bạch (Citation Tracking): AI đính kèm nguồn tham khảo chi tiết ở cuối câu trả lời, bao gồm tên file gốc và số trang để người dùng dễ dàng đối chiếu.
- Xử lý hoàn toàn Local: Không gửi dữ liệu lên cloud, bảo vệ an toàn tuyệt đối cho tài liệu nội bộ.

## Công nghệ sử dụng

| Thành phần                       | Công nghệ                                    |
| -------------------------------- | -------------------------------------------- |
| Backend                          | Django 5.0.6                                 |
| Frontend                         | HTML5, TailwindCSS, JavaScript               |
| Database                         | SQLite3                                      |
| LLM                              | Qwen2.5:7b (Ollama)                          |
| Framework RAG                    | LangChain                                    |
| Vector Store (Semantic Search)   | FAISS                                        |
| Keyword Search                   | BM25 (rank_bm25)                             |
| Embedding Model (Bi-encoder)     | HuggingFace Embeddings                       |
| Re-ranking Model (Cross-encoder) | sentence-transformers/ms-marco-MiniLM-L-6-v2 |
| Document Parsers                 | pdfplumber, docx2txt                         |

## Yêu cầu hệ thống

### Phần cứng

- CPU: 4 cores trở lên (Khuyến nghị 8 cores)
- RAM: Tối thiểu 16GB (Khuyến nghị 32GB để chạy mượt model 7B)
- Ổ cứng: Trống tối thiểu 15GB
- GPU: Không bắt buộc (Khuyến nghị có GPU tối thiểu 6GB VRAM để tăng tốc xử lý model)

### Phần mềm

- Hệ điều hành: Windows 11, macOS 11+, hoặc Linux (Ubuntu 20.04+)
- Python: Phiên bản 3.12.10 trở lên
- Git: Để quản lý mã nguồn

## Hướng dẫn cài đặt

### Bước 1: Tải mã nguồn

```
git clone <repository-url>
cd smartdoc-ai
```

### Bước 2: Khởi tạo môi trường ảo (Virtual Environment)

Hệ điều hành Windows:

```
python -m venv venv
venv\Scripts\activate
```

Hệ điều hành macOS/Linux:

```
python3 -m venv venv
source venv/bin/activate
```

### Bước 3: Cài đặt thư viện phụ thuộc

```
pip install -r requirements.txt
```

### Bước 4: Cài đặt và cấu hình Ollama

Truy cập https://ollama.com/download và tải phiên bản cài đặt trực tiếp phù hợp với hệ điều hành của bạn. Sau khi cài đặt xong, mở Terminal hoặc Command Prompt và chạy lệnh sau để tải model:

```cmd
ollama serve
ollama pull qwen2.5:7b
```

### Bước 5: Cấu hình cơ sở dữ liệu và thư mục

```cmd
python manage.py makemigrations
python manage.py migrate
```

### Bước 6: Khởi chạy ứng dụng

```cmd
python manage.py runserver
```

Truy cập ứng dụng thông qua trình duyệt tại địa chỉ: http://127.0.0.1:8000

## Hướng dẫn sử dụng (Theo luồng trải nghiệm - User Flow)

Hệ thống được thiết kế theo luồng trải nghiệm người dùng liền mạch qua 3 trang chính:

### Trang chủ (Home) - Bắt đầu truy cập

- Lần đầu truy cập: Nhập tên hiển thị của bạn vào biểu mẫu và nhấn nút bắt đầu để hệ thống định danh.
- Truy cập lần sau: Hệ thống tự động ghi nhớ thông tin, bạn chỉ cần nhấn "Vào trò chuyện ngay".
- Tùy chỉnh: Có thể thay đổi tên người dùng bất cứ lúc nào qua nút "Đổi tên người dùng".

### Bảng điều khiển (Dashboard) - Quản lý hội thoại

Sau khi vào hệ thống, bạn sẽ quản lý các luồng công việc tại đây:

- Tạo phiên làm việc mới: Nhấn "Trò chuyện mới" để mở một phiên chat hoàn toàn trống.
- Tiếp tục công việc: Click vào một thẻ hội thoại cũ trong danh sách. Lịch sử và tài liệu của hội thoại này đã được lưu trữ an toàn và sẵn sàng để sử dụng tiếp.
- Cập nhật thông tin: Rê chuột vào từng hội thoại để hiển thị công cụ Đổi tên (đặt tên gợi nhớ như "Phân tích Hợp đồng A") hoặc Xóa (xóa bỏ hoàn toàn phiên làm việc).

### Không gian Trò chuyện (Chat View) - Tương tác AI

Đây là nơi diễn ra các tương tác chính với AI. Luồng công việc tại trang này diễn ra theo 3 bước:

**Bước 1: Nạp cơ sở tri thức (Tải tài liệu)**

- Tại thanh công cụ bên phải, nhấn chọn và tải lên các tài liệu cần phân tích (hỗ trợ PDF, DOCX).
- Tính năng Upload cộng dồn: Bạn có thể tải lên các file ban đầu, sau đó trong quá trình trò chuyện nếu phát sinh thêm tài liệu mới, bạn cứ tiếp tục tải lên. Hệ thống sẽ tự động gộp nội dung mới vào cơ sở dữ liệu vector chung của phiên chat hiện tại mà không ghi đè dữ liệu cũ.

**Bước 2: Truy vấn thông tin (Hỏi đáp với AI)**

- Nhập câu hỏi vào khung chat ở giữa màn hình.
- AI sẽ tiến hành rà soát hàng ngàn trang tài liệu bằng bộ máy Hybrid Search và đưa ra câu trả lời.
- Kiểm chứng thông tin: Dưới mỗi câu trả lời của AI luôn có phần "Nguồn tham khảo". Bạn có thể đọc tên file và trang số mấy để đối chiếu trực tiếp với tài liệu gốc, đảm bảo tính minh bạch.

**Bước 3: Quản lý tiện ích trong quá trình Chat**

- Phục hồi phiên làm việc (F5): Khi bạn tải lại trang, hệ thống tự động nạp lại toàn bộ tài liệu từ ổ cứng (Persistent Vector Storage) lên RAM để bạn tiếp tục hỏi đáp ngay lập tức.
- Xem lại câu hỏi: Cột bên trái lưu trữ danh sách các câu hỏi bạn đã hỏi. Click vào một câu hỏi cũ để AI điền lại nội dung đó vào khung chat.
- Dọn dẹp: Sử dụng nút "Xóa lịch sử" (chỉ làm sạch khung chat) hoặc "Xóa tài liệu" (xóa toàn bộ file để nạp bộ tài liệu hoàn toàn mới) khi cần chuyển hướng công việc.

## Cấu trúc dự án

```
smartdoc-ai/
├── chat_project/          # Cấu hình Django (settings, urls)
├── core/                  # Ứng dụng lõi
│   ├── models.py          # Lược đồ cơ sở dữ liệu
│   ├── views/             # Logic điều hướng và API
│   ├── services/          # Business logic
│   │   ├── rag_service.py # Xử lý Pipeline RAG
│   │   └── db_service.py  # Giao tiếp với Database
│   └── migrations/        # Migrate DB
├── templates/             # Giao diện người dùng (HTML)
├── media/                 # Thư mục gốc lưu trữ tài nguyên
│   ├── pdfs/              # Chứa các file PDF và DOCX được tải lên
│   └── vectorstores/      # Chứa cơ sở dữ liệu FAISS Index và BM25 chunks
├── static/                # Tài nguyên tĩnh (CSS, JS, Images)
├── manage.py              # Công cụ quản lý Django
└── requirements.txt       # Danh sách thư viện Python
```

## Tùy chỉnh nâng cao

### Tùy chỉnh tham số Hybrid Search & Re-ranking

Trong file `core/services/rag_service.py`:

```
# Thay đổi mô hình Re-ranking
self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

# Tùy chỉnh số lượng ứng viên truy xuất (K)
faiss_docs = self.vector_store.similarity_search(question, k=10) # Lượng ứng viên Semantic
bm25_docs = self.bm25.get_top_n(tokenized_query, self.chunks, n=10) # Lượng ứng viên Keyword
# Hệ thống sẽ gom các ứng viên này, chấm điểm lại và chọn top 3
```

### Tùy chỉnh chia nhỏ văn bản (Chunking)

Trong file `core/services/rag_service.py`:

```
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,  # Kích thước mỗi đoạn
    chunk_overlap=200 # Độ lặp lại giữa các đoạn
)
```

## Giao diện hệ thống

![onboarding1](/static/aichathomepage1.png)
![onboarding1](static/aichathomepage2.png)
![onboarding1](static/aichatdashboard.png)
![onboarding1](static/aichatbox.png)

**Chúc bạn sử dụng ứng dụng vui vẻ! 🎉**
