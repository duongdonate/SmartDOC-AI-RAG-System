import os
import tempfile
import logging
import random
import time
from typing import Dict, Any, List, Optional
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

class RAGService:
    """RAGService tối ưu cho qwen2.5:1.5b - Hỗ trợ PDF, DOCX và tùy chỉnh Chunk Strategy"""

    def __init__(self):
        self.vector_store = None
        self.retriever = None
        self.chain = None
        self.embedding_model = None
        self.llm = None
        self.cache = {}
        self.cache_timestamp = {}
        self.current_file_type = None
        self.current_file_name = None
        
        # Cấu hình chunk mặc định
        self.chunk_size = 900
        self.chunk_overlap = 80

        self._init_embedding_model()
        self._init_llm()

    def _init_embedding_model(self):
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True, 'batch_size': 64}
        )
        print("✓ Embedding model (nhẹ) sẵn sàng")

    def _init_llm(self):
        """Cấu hình 1.5B tối ưu tốc độ + tự nhiên"""
        self.llm = Ollama(
            model="qwen2.5:1.5b",
            base_url="http://localhost:11434",
            temperature=0.35,
            top_p=0.88,
            repeat_penalty=1.12,
            num_predict=380,
            num_ctx=1536,
            num_thread=4,
        )
        print("✓ Ollama qwen2.5:1.5b đã tối ưu tốc độ")

    def _get_file_type(self, file_name: str) -> str:
        """Xác định loại file dựa trên phần mở rộng"""
        ext = file_name.lower().split('.')[-1]
        if ext == 'pdf':
            return 'pdf'
        elif ext == 'docx':
            return 'docx'
        else:
            return 'unknown'

    def _load_document(self, file_path: str, file_type: str) -> List[Document]:
        """Load document dựa trên loại file (PDF hoặc DOCX)"""
        if file_type == 'pdf':
            loader = PDFPlumberLoader(file_path)
            documents = loader.load()
            for i, doc in enumerate(documents):
                if 'page' not in doc.metadata:
                    doc.metadata['page'] = i + 1
                doc.metadata['file_type'] = 'pdf'
            return documents
        elif file_type == 'docx':
            loader = Docx2txtLoader(file_path)
            documents = loader.load()
            for i, doc in enumerate(documents):
                doc.metadata['page'] = i + 1
                doc.metadata['file_type'] = 'docx'
            return documents
        else:
            raise ValueError(f"Không hỗ trợ loại file: {file_type}")

    def update_chunk_config(self, chunk_size: int, chunk_overlap: int) -> bool:
        """Cập nhật cấu hình chunk"""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        print(f"✓ Đã cập nhật chunk config: size={chunk_size}, overlap={chunk_overlap}")
        return True

    def get_chunk_config(self) -> Dict[str, int]:
        """Lấy cấu hình chunk hiện tại"""
        return {
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap
        }

    def process_document_with_config(self, file, file_name: str, chunk_size: int = None, chunk_overlap: int = None) -> bool:
        """Xử lý tài liệu với cấu hình chunk tùy chỉnh"""
        use_chunk_size = chunk_size if chunk_size else self.chunk_size
        use_chunk_overlap = chunk_overlap if chunk_overlap else self.chunk_overlap
        
        tmp_path = None
        try:
            file_type = self._get_file_type(file_name)
            print(f"📄 Đang xử lý {file_type.upper()}: {file_name}")
            print(f"⚙️ Chunk config: size={use_chunk_size}, overlap={use_chunk_overlap}")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_type}') as tmp_file:
                for chunk in file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name

            documents = self._load_document(tmp_path, file_type)
            
            if not documents:
                raise ValueError(f"Không thể đọc nội dung từ {file_name}")

            print(f"✓ Đã đọc {len(documents)} {'trang' if file_type == 'pdf' else 'đoạn'}")

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=use_chunk_size,
                chunk_overlap=use_chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""]
            )

            chunks = text_splitter.split_documents(documents)
            print(f"✓ Đã chia thành {len(chunks)} chunks")

            self.vector_store = FAISS.from_documents(chunks, self.embedding_model)

            self.retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 2}
            )

            prompt_template = """Bạn là trợ lý thân thiện, trả lời ngắn gọn nhưng đầy đủ và tự nhiên bằng tiếng Việt.

YÊU CẦU RẤT QUAN TRỌNG:
- Trả lời đúng và trực tiếp vào câu hỏi
- Độ dài: 3-5 câu (khoảng 100-150 từ), không được quá ngắn
- Dùng thông tin từ ngữ cảnh nếu có và có thể bổ sung thêm kiến thức chung để trả lời tự nhiên hơn
- Nếu không có thông tin liên quan, hãy trả lời tự nhiên dựa trên kiến thức chung, logic và hữu ích
- Viết mạch lạc, gần gũi như đang nói chuyện

Ngữ cảnh:
{context}

Câu hỏi: {question}

Trả lời ngay (3-5 câu, tự nhiên): """

            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["context", "question"]
            )

            def format_docs(docs: List[Document]) -> str:
                if not docs:
                    return "Không có thông tin liên quan trong tài liệu."
                formatted = []
                for doc in docs[:2]:
                    content = doc.page_content[:420]
                    page_num = doc.metadata.get('page', '?')
                    formatted.append(f"[Trang {page_num}] {content}")
                return "\n\n".join(formatted)

            self.chain = (
                {
                    "context": self.retriever | RunnableLambda(format_docs),
                    "question": RunnablePassthrough()
                }
                | prompt
                | self.llm
                | StrOutputParser()
            )

            self.current_file_type = file_type
            self.current_file_name = file_name
            self.cache.clear()
            
            print(f"✓ {file_type.upper()} đã xử lý xong ({len(chunks)} chunks)")
            return True

        except Exception as e:
            print(f"✗ Lỗi xử lý {file_name}: {e}")
            return False
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def process_document(self, file, file_name: str) -> bool:
        """Xử lý tài liệu với cấu hình chunk hiện tại"""
        return self.process_document_with_config(file, file_name, self.chunk_size, self.chunk_overlap)

    def process_pdf(self, pdf_file) -> bool:
        """Tương thích ngược - gọi process_document"""
        return self.process_document(pdf_file, getattr(pdf_file, 'name', 'document.pdf'))

    def ask_question(self, question: str) -> Dict[str, Any]:
        """Trả lời nhanh + cache + đảm bảo độ dài + hiển thị số trang"""
        if not self.chain or not self.retriever:
            return {"answer": self._get_quick_answer(question), "sources": []}

        cache_key = question.lower().strip()
        if cache_key in self.cache:
            if time.time() - self.cache_timestamp.get(cache_key, 0) > 1200:
                del self.cache[cache_key]
            else:
                return self.cache[cache_key]

        try:
            source_docs = self.retriever.invoke(question)
            answer = self.chain.invoke(question)

            if len(answer.split()) < 45:
                answer = self._lengthen_answer(answer, question)

            sources = []
            for doc in source_docs[:2]:
                page_number = doc.metadata.get('page', '?')
                file_type = doc.metadata.get('file_type', self.current_file_type or 'pdf')
                sources.append({
                    'content': doc.page_content[:180] + '...' if len(doc.page_content) > 180 else doc.page_content,
                    'page_number': page_number,
                    'file_type': file_type,
                    'metadata': doc.metadata
                })

            result = {"answer": answer, "sources": sources}

            self.cache[cache_key] = result
            self.cache_timestamp[cache_key] = time.time()

            return result

        except Exception as e:
            print(f"✗ Lỗi ask_question: {e}")
            return {"answer": self._get_quick_answer(question), "sources": []}

    def _lengthen_answer(self, short_answer: str, question: str) -> str:
        """Thêm nội dung tự nhiên để đủ độ dài"""
        fillers = [
            " Ngoài ra, bạn có thể xem xét thêm rằng ",
            " Trong thực tế, điều này thường được áp dụng như sau: ",
            " Tóm lại, đây là hướng xử lý hợp lý nhất cho trường hợp của bạn.",
            " Điều quan trọng là cần lưu ý thêm một chút về "
        ]
        return short_answer.strip() + random.choice(fillers)

    def _get_quick_answer(self, question: str) -> str:
        """Fallback khi chưa có tài liệu"""
        templates = [
            f"Về câu hỏi '{question}', tôi xin trả lời ngắn gọn như sau: Đây là vấn đề quan trọng và cần được xem xét kỹ. Thông thường, cách tốt nhất là tập trung vào các yếu tố chính và thực hiện từng bước một cách logic.",
            f"Câu hỏi '{question}' rất hay. Theo kinh nghiệm chung, bạn nên bắt đầu từ những điểm cơ bản nhất rồi mở rộng dần. Như vậy sẽ đảm bảo kết quả tốt và dễ thực hiện hơn."
        ]
        return random.choice(templates)

    def get_document_info(self) -> Dict[str, Any]:
        """Lấy thông tin document hiện tại"""
        return {
            'file_name': self.current_file_name,
            'file_type': self.current_file_type,
            'has_document': self.vector_store is not None
        }

    def clear(self):
        self.vector_store = None
        self.retriever = None
        self.chain = None
        self.cache.clear()
        self.cache_timestamp.clear()
        self.current_file_type = None
        self.current_file_name = None
        print("✓ RAG service đã xóa sạch")

# Singleton
rag_service = RAGService()