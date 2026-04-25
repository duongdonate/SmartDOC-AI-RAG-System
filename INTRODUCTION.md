# DANH SÁCH TÍNH NĂNG VÀ LUỒNG HOẠT ĐỘNG ỨNG DỤNG AI CHAT (SMARTDOC)

## 1. TỔNG QUAN HỆ THỐNG

### 1.1. TRANG CHỦ (HOME)

- Giao diện giới thiệu: Được thiết kế tinh gọn, hiện đại, đóng vai trò là điểm chạm đầu tiên giới thiệu tổng quan về sức mạnh của ứng dụng AI Chat API.
- Định danh người dùng (User Identification): Tự động kiểm tra database để mang lại trải nghiệm cá nhân hóa liền mạch. Nếu là người dùng mới, hệ thống hiển thị form nhập tên thân thiện. Nếu đã có dữ liệu từ các phiên trước, hệ thống nhận diện và hiển thị ngay nút "Vào trò chuyện ngay", giúp tiết kiệm thao tác khởi động.
- Quản lý phiên đồng bộ: Lưu thông tin định danh vào Database (Back-end) và LocalStorage (Front-end) để đồng bộ hóa, đảm bảo trải nghiệm xuyên suốt ngay cả khi người dùng mở ứng dụng trên nhiều tab trình duyệt khác nhau.
- Cập nhật thông tin: Nút "Đổi tên người dùng" cho phép cập nhật thông tin định danh linh hoạt bất cứ lúc nào, thay đổi sẽ được phản ánh ngay lập tức trên toàn hệ thống.

### 1.2. BẢNG ĐIỀU KHIỂN (DASHBOARD)

#### Quản lý hội thoại toàn diện:

- Hiển thị danh sách trực quan: Trình bày dưới dạng Grid layout 2 cột giúp tối ưu hóa không gian hiển thị trên màn hình lớn. Mỗi thẻ (card) cung cấp đầy đủ thông tin tóm tắt: tiêu đề hội thoại, đoạn trích câu hỏi xem trước (preview) để dễ nhận biết, thời gian cập nhật gần nhất và tổng số lượng tin nhắn đã trao đổi.
- Khởi tạo nhanh chóng: Nút "Trò chuyện mới" được đặt ở vị trí nổi bật, cho phép người dùng khởi tạo ngay lập tức một phiên không gian làm việc (conversation) hoàn toàn mới và độc lập về mặt dữ liệu.
- Cập nhật tiêu đề linh hoạt: Hỗ trợ đổi tên hội thoại qua Modal popup. Việc đổi tên giúp phân loại các dự án dễ dàng hơn (ví dụ: "Phân tích báo cáo Q1", "Tra cứu luật lao động"). UI sẽ cập nhật tức thì ngay sau khi lưu mà không cần tải lại toàn bộ trang.
- Xóa hội thoại an toàn: Cung cấp cơ chế xóa bỏ triệt để. Khi xác nhận xóa qua hộp thoại cảnh báo, hệ thống sẽ dọn dẹp sạch sẽ toàn bộ dữ liệu liên quan ở cả Database (tin nhắn) và ổ cứng vật lý (file PDF/DOCX, vector database), ngăn chặn rò rỉ dữ liệu và giải phóng không gian lưu trữ.

### 1.3. KHÔNG GIAN TRÒ CHUYỆN (CHAT VIEW)

#### Quản lý tài liệu đa chiều (Incremental Document Management):

- Xử lý đa định dạng chuyên sâu: Hỗ trợ phân tách và bóc tách dữ liệu phức tạp từ file PDF (thông qua engine pdfplumber để giữ cấu trúc đoạn văn) và file DOCX truyền thống.
- Tải lên cộng dồn (Incremental Upload): Đây là tính năng khác biệt lớn nhất. Cho phép tải lên nhiều file cùng lúc. Ví dụ: Người dùng đang hỏi đáp về "Quy chế công ty phần 1", sau đó có thể tải tiếp "Quy chế phần 2" lên ngay trong lúc đang chat. Hệ thống sẽ tự động gộp (append) nội dung mới vào cơ sở dữ liệu vector chung của phiên đó mà tuyệt đối không ghi đè hay làm mất đi dữ liệu của file cũ.
- Tự động phục hồi (Auto-recovery) chống mất mát dữ liệu: Nếu người dùng lỡ tay đóng tab hoặc nhấn làm mới trang (F5), hệ thống sẽ tự động nạp lại toàn bộ file văn bản và Vector Store từ ổ cứng (Persistent Storage) lên RAM. Quá trình này diễn ra trong chớp mắt, cho phép tiếp tục hỏi đáp ngay lập tức mà không phải tốn thời gian upload hay nhúng (embedding) lại từ đầu.
- Phân biệt trực quan: Card hiển thị tài liệu sử dụng mã màu UI/UX chuyên biệt (Xanh lá biểu tượng cho PDF, Xanh dương biểu tượng cho DOCX), giúp người dùng dễ dàng kiểm soát danh sách các file đang được phân tích.

#### Cấu hình thuật toán chia nhỏ (Chunking Strategy):

- Giao diện tùy chỉnh trực quan: Cung cấp Slider cho phép người dùng (đặc biệt là người dùng chuyên môn) can thiệp trực tiếp vào thuật toán băm dữ liệu để phù hợp với từng loại tài liệu cụ thể:
  - Chunk Size (Từ 600 → 1500, Mặc định: 900): Kích thước chunk lớn giúp bảo toàn ngữ cảnh rộng (phù hợp báo cáo văn học/phân tích), trong khi chunk nhỏ giúp lấy ra các thông tin chi tiết, chính xác (phù hợp với hợp đồng pháp lý, bảng biểu).
  - Chunk Overlap (Từ 50 → 150, Mặc định: 80): Độ lặp lại giữa các đoạn giúp chống việc các ý nghĩa bị cắt đứt làm đôi ở giữa hai đoạn văn.
- Xử lý lại đồng bộ (Re-process): Khi thay đổi thông số, hệ thống sẽ tiến hành dọn dẹp index cũ, cập nhật cấu hình và băm lại toàn bộ danh sách tài liệu đang có một cách tự động.

#### Tương tác AI và Hỏi đáp (RAG Pipeline):

- Cơ chế tìm kiếm lai (Hybrid Search) mạnh mẽ: Khi một câu hỏi được gửi đi, hệ thống kích hoạt song song 2 luồng tìm kiếm bổ trợ cho nhau: Tìm kiếm theo Ngữ nghĩa (Vector) để hiểu ý định của người dùng, và Tìm kiếm theo Từ khóa (Keyword) để bắt chính xác các danh từ riêng, mã số hợp đồng, hay các thuật ngữ đặc thù mà mô hình vector dễ bỏ sót.
- Hiển thị phản hồi: Cấu trúc Bubble chat hiện đại, phân biệt rõ ràng luồng tin nhắn giữa User và Assistant với định dạng văn bản Markdown sắc nét (hỗ trợ in đậm, in nghiêng, danh sách).
- Trích dẫn minh bạch (Citation Tracking): Giải quyết triệt để vấn đề "hộp đen" của AI. Hệ thống luôn đính kèm nguồn gốc dữ liệu ở cuối câu trả lời theo định dạng chuẩn mực: `[Tên_File.pdf] (Trang X): "Nội dung trích xuất nguyên bản..."`. Điều này cho phép người dùng đối chiếu, xác minh thông tin gốc một cách dễ dàng và tăng độ tin cậy của hệ thống lên mức tối đa.
- Lưu trữ toàn vẹn: Không chỉ lưu trữ câu trả lời, hệ thống ghi nhận toàn bộ metadata của nguồn tham khảo vào Database để đảm bảo tính minh bạch lâu dài khi người dùng xem lại lịch sử.

#### Lịch sử hiển thị:

- Sidebar lịch sử (Trái): Hiển thị danh sách 15 câu hỏi gần nhất trong phiên. Tính năng này giúp người dùng dễ dàng theo dõi mạch tư duy của mình. Click vào một câu hỏi cũ để tự động điền lại vào khung input, tiết kiệm công sức gõ phím.
- Sidebar tài liệu (Phải): Bảng điều khiển quản lý toàn bộ trạng thái, dung lượng và danh sách các file đang được hệ thống phân tích trong thời gian thực.

## 2. HỆ THỐNG DATABASE

### Cấu trúc Models liên kết chặt chẽ:

1. User: Bảng lưu trữ và quản lý định danh người dùng cốt lõi.
2. Conversation: Quản lý siêu dữ liệu (metadata) của từng phiên làm việc (Bao gồm Tổng số tin nhắn đã chat, tổng số tài liệu đã nạp, và timestamp cập nhật gần nhất để sắp xếp trên Dashboard).
3. Document: Lưu vết chi tiết của từng file vật lý (Tên file gốc, đường dẫn lưu trữ an toàn trên server, và dung lượng định dạng byte).
4. Message: Bảng lưu trữ chi tiết nhất, bao gồm luồng hội thoại (Role: User/Assistant), nội dung text, và một trường JSON riêng biệt để lưu trữ mảng các nguồn trích dẫn (citations).

### Hệ thống lưu trữ vật lý được cô lập:

- An toàn dữ liệu: File tài liệu được lưu cô lập hoàn toàn tại `media/pdfs/{conversation_id}/`. Việc chia thư mục theo ID phiên chat đảm bảo không có sự xung đột tên file giữa các cuộc hội thoại khác nhau.
- Vector lưu trữ: Cơ sở dữ liệu Vector được kết xuất thành file vật lý, lưu FAISS Index và BM25 chunks tại `media/vectorstores/{conversation_id}/`.

## 3. HỆ THỐNG RAG

### Giai đoạn 1: Tiền xử lý dữ liệu (Pre-processing)

- Băm dữ liệu thông minh: Áp dụng thuật toán `RecursiveCharacterTextSplitter`. Khác với các thuật toán cắt chuỗi cơ bản, thuật toán này ưu tiên cắt văn bản tại các dấu chấm câu, dấu xuống dòng, giúp bảo toàn tối đa tính toàn vẹn ngữ nghĩa của một câu hoặc một đoạn văn.
- Xây dựng Index song song: Đây là trái tim của kiến trúc tìm kiếm lai:
  - Tạo FAISS Vector Index: Chuyển đổi văn bản thành các ma trận số học thông qua HuggingFace Embeddings (Dùng để bắt các ngữ nghĩa tương đồng).
  - Tạo BM25 Tokenized Corpus: Xây dựng bộ từ điển đảo ngược dựa trên tần suất xuất hiện của từ ngữ (Dùng để bắt chính xác các keyword hiếm, từ khóa chuyên ngành).

### Giai đoạn 2: Truy xuất và Chấm điểm (Retrieval & Re-ranking)

- Pooling (Gom ứng viên sơ cấp): Thuật toán FAISS được gọi để lấy top 10 đoạn văn có ý nghĩa sát nhất. Đồng thời, thuật toán BM25 gọi top 10 đoạn văn khớp từ khóa nhất. Hệ thống sẽ gộp 20 đoạn văn này lại, loại bỏ các đoạn trùng lặp.
- Cross-Encoder Re-ranking (Sàng lọc thứ cấp): Thay vì đưa cả một đống dữ liệu hỗn tạp cho LLM, hệ thống sử dụng mô hình `ms-marco-MiniLM-L-6-v2` như một màng lọc tinh xảo. Mô hình này sẽ đọc đối chiếu (Cross-attention) chi tiết từng từ giữa Câu hỏi và từng Đoạn văn ứng viên để chấm điểm lại mức độ liên quan. Sau quá trình sàng lọc gắt gao, chỉ 3 ứng viên xuất sắc nhất, chứa đựng thông tin chính xác nhất mới được giữ lại.

### Giai đoạn 3: Sinh văn bản (Generation)

- LLM Runtime: Sử dụng sức mạnh của mô hình ngôn ngữ lớn Qwen2.5:7b, được triển khai chạy hoàn toàn nội bộ qua nền tảng Ollama.
- Prompt Engineering chống ảo giác: Prompt được thiết kế cực kỳ khắt khe, ép buộc LLM chỉ được phép phân tích và tổng hợp câu trả lời hoàn toàn dựa trên 3 đoạn văn bản (context) đã được cung cấp từ Giai đoạn 2. Hệ thống xử lý các câu hỏi một cách độc lập và cô lập, cấm tuyệt đối hành vi ảo giác (hallucination) hay bịa đặt thông tin ngoài luồng.

## 4. HỆ THỐNG API ENDPOINT

Toàn bộ hệ thống giao tiếp thông qua kiến trúc RESTful chuẩn mực, phân tách rõ ràng giữa việc tải giao diện và trao đổi dữ liệu JSON.

### Page Views (Giao diện):

| Endpoint      | Phương thức | Chức năng                                                           |
| ------------- | ----------- | ------------------------------------------------------------------- |
| `/`           | GET         | Render trang Home đầu vào                                           |
| `/dashboard/` | GET         | Render trang Dashboard quản lý tổng thể                             |
| `/chat/`      | GET         | Khởi tạo giao diện Chat mới hoàn toàn trống                         |
| `/chat/<id>/` | GET         | Nạp và tải lại giao diện Chat cùng với toàn bộ dữ liệu của phiên cũ |

### REST API:

| Endpoint                    | Phương thức | Chức năng                                                                          |
| --------------------------- | ----------- | ---------------------------------------------------------------------------------- |
| `/api/upload/`              | POST        | Nhận file multipart/form-data, lưu trữ vật lý và kích hoạt tiến trình băm tài liệu |
| `/api/ask/`                 | POST        | Gửi câu hỏi của người dùng và kích hoạt toàn bộ chuỗi Pipeline RAG                 |
| `/api/clear-history/`       | POST        | Xóa sạch lịch sử tin nhắn hiển thị trong phiên làm việc hiện tại                   |
| `/api/clear-document/`      | POST        | Xóa toàn bộ file vật lý và vector index của phiên để làm mới bộ nhớ                |
| `/api/get-questions/`       | GET         | Lấy danh sách giới hạn các câu hỏi gần đây để hiển thị lên Sidebar                 |
| `/api/get-conversations/`   | GET         | Lấy toàn bộ danh sách phiên chat để render giao diện Dashboard                     |
| `/api/get-user/`            | GET         | Truy xuất thông tin định danh của người dùng hiện tại                              |
| `/api/update-user-name/`    | POST        | Lưu trữ tên định danh mới cập nhật vào Database                                    |
| `/api/rename-conversation/` | POST        | Thay đổi metadata tiêu đề của một phiên chat cụ thể                                |
| `/api/delete-conversation/` | POST        | Kích hoạt chuỗi hành động xóa an toàn toàn bộ dữ liệu của một phiên                |
| `/api/get-chunk-config/`    | GET         | Lấy cấu hình Text Splitter (Size, Overlap) đang áp dụng hiện tại                   |
| `/api/update-chunk-config/` | POST        | Lưu cấu hình băm văn bản mới và trả về trạng thái                                  |

## 5. GIAO DIỆN VÀ TRẢI NGHIỆM NGƯỜI DÙNG (UI/UX)

- Thiết kế hiện đại: Sử dụng bộ framework TailwindCSS giúp giao diện được thiết kế theo tư duy Mobile-first, hiển thị sắc nét, tốc độ tải trang cực nhanh và co giãn mượt mà trên đa dạng kích thước thiết bị.
- Phản hồi trạng thái tinh tế (Feedback): Giải quyết tâm lý chờ đợi của người dùng qua hệ thống phản hồi thị giác: hiển thị Spinner loading khi đang băm tài liệu nặng, thông báo "Đang suy nghĩ..." khi AI đang xử lý câu hỏi, và các Toast notification bật góc màn hình khi thực hiện thao tác thành công hoặc gặp lỗi.
- Bảo vệ người dùng (Failsafe): Các hành động phá hủy dữ liệu (như Xóa chat, Xóa file, Xử lý lại tài liệu) luôn đi kèm với Tooltip giải thích chi tiết khi hover chuột và các Modal xác nhận (Confirmation) cảnh báo màu đỏ nhằm ngăn chặn các thao tác sai lầm ngoài ý muốn.
- Tự động hóa UI: Tính năng Auto-scroll lập tức cuộn màn hình xuống tin nhắn mới nhất, giữ cho tiêu điểm làm việc của người dùng luôn tập trung.

## 6. CÔNG NGHỆ SỬ DỤNG

### Backend & AI Pipeline

Sự kết hợp giữa framework truyền thống bền bỉ và các thư viện AI hiện đại:

- Framework điều hướng: Django 5.0.6
- RAG Orchestration: LangChain
- Vector Database (Lưu trữ nhúng chiều cao): FAISS
- Keyword Search: rank_bm25
- Bi-encoder Model (Nhúng ngữ nghĩa): HuggingFace Embeddings
- Cross-encoder Model (Chấm điểm chéo): sentence-transformers
- LLM Runtime: Ollama (Qwen2.5:7b)

### Frontend & Storage

- Giao diện (UI): HTML5, TailwindCSS, Vanilla JavaScript (Tối ưu hóa, không dùng library thừa)
- Database Relational: SQLite3
- File Parsing (Trích xuất văn bản thô): pdfplumber, docx2txt

## 7. CÁC TÍNH NĂNG ĐỘT PHÁ (V2 UPGRADES)

| STT | Tính năng lõi        | Mô tả kỹ thuật chuyên sâu                                                                                                                                                            |
| --- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Hybrid Search        | Kết hợp sức mạnh của FAISS (bắt ngữ cảnh) và BM25 (bắt từ khóa chính xác), tạo ra thuật toán tìm kiếm cân bằng và vượt trội hơn so với Semantic Search truyền thống.                 |
| 2   | Cross-Encoder Rerank | Tái thẩm định các đoạn văn bản ứng viên thu thập được để loại bỏ nhiễu thông tin, đảm bảo LLM nhận được những đoạn trích dẫn (context) có chất lượng và độ chính xác tuyệt đối nhất. |
| 3   | Incremental Upload   | Kiến trúc xây dựng thuật toán đột phá cho phép tải thêm nhiều tài liệu mới và gộp chung liên tục vào Index đang chạy, tạo ra bộ lưu trữ tri thức khổng lồ theo thời gian.            |
| 4   | Persistent Vector DB | Hệ thống lưu trữ trạng thái cấu trúc Vector trực tiếp xuống ổ cứng cứng. Giúp bỏ qua bước tính toán nhúng (embedding) tốn kém tài nguyên mỗi khi reload hoặc mở lại phiên chat cũ.   |
| 5   | Exact Citation       | Khả năng thu thập và trả về metadata cực kỳ chi tiết đến từng số trang cụ thể và tên file gốc để người dùng trực tiếp kiểm chứng sự thật, chống lại hiện tượng "hallucination".      |

## 8. BẢNG THỐNG KÊ TÍNH NĂNG

| Loại dữ liệu cấu thành        | Số lượng thống kê                              |
| ----------------------------- | ---------------------------------------------- |
| Màn hình giao diện chính      | 3 trang                                        |
| Lược đồ Database (Models)     | 4 đối tượng lõi                                |
| API Endpoints                 | 16 Endpoints                                   |
| Tính năng lõi (RAG V2)        | 5 Module chính                                 |
| Các tương tác UI/UX           | 15+ Behavior                                   |
| **Tổng quan quy mô hệ thống** | **Đạt cấp độ Dự án Hệ thống Phần mềm Thực tế** |
