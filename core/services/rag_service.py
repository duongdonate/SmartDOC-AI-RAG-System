import os
import shutil
import tempfile
import logging
import random
import time
import json
import pickle
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
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
from typer.cli import docs
from django.conf import settings

logger = logging.getLogger(__name__)

class RAGService:
    """RAGService tối ưu cho qwen2.5:7b - Hỗ trợ PDF, DOCX và tùy chỉnh Chunk Strategy"""

    def __init__(self):
        self.vector_store = None
        self.retriever = None
        self.chain = None
        self.embedding_model = None
        self.bm25 = None
        self.llm = None
        self.cache = {}
        self.cache_timestamp = {}
        self.current_file_types = []
        self.current_file_names = []
        
        # Cấu hình chunk mặc định
        self.chunk_size = 700
        self.chunk_overlap = 100
        self.chunks = []

        self._init_embedding_model()
        self._init_llm()
        self._init_cross_encoder()

    def _init_embedding_model(self):
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("✓ Embedding model (nhẹ) sẵn sàng")

    def _init_llm(self):
        """Cấu hình 1.5B tối ưu tốc độ + tự nhiên"""
        self.llm = Ollama(
            model="qwen2.5:7b",
            base_url="http://localhost:11434",
            temperature=0.3,               # Độ sáng tạo của câu trả lời 
            top_p=0.9,                     # Nucleus sampling để lọc các từ có xác suất thấp 
            num_thread=8,
            num_gpu=100,                   # Sử dụng GPU nếu có, tự động fallback CPU nếu không 
            num_ctx=2048,                  # Tăng context window để xử lý tốt hơn các tài liệu dài 
            repeat_penalty=1.1             # Hạn chế việc mô hình bị lặp từ trong câu trả lời 
        )
        print("✓ Ollama qwen2.5:7b đã tối ưu tốc độ")

    def _init_cross_encoder(self):
        # Dùng model nhẹ và hiệu quả như project cũ của bạn, hoặc dùng BAAI/bge-reranker-v2-m3
        self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        print("✓ Cross-Encoder (SentenceTransformers) sẵn sàng")
    
    
    def _build_chain(self):

        prompt_template = """
        Bạn là một chuyên gia phân tích tài liệu chuyên nghiệp.
        Nhiệm vụ của bạn là trả lời câu hỏi của người dùng DỰA VÀO DUY NHẤT ngữ cảnh (Context) được cung cấp dưới đây.

        Context:
        {context}

        Question:
        {question}

        🚨 CÁC QUY TẮC BẮT BUỘC PHẢI TUÂN THỦ (NẾU VI PHẠM SẼ BỊ PHẠT):
        1. NGÔN NGỮ: BẠN PHẢI LUÔN LUÔN TRẢ LỜI BẰNG TIẾNG VIỆT (VIETNAMESE). TUYỆT ĐỐI KHÔNG ĐƯỢC SỬ DỤNG TIẾNG TRUNG HOẶC BẤT KỲ NGÔN NGỮ NÀO KHÁC.
        2. SỰ THẬT: Chỉ sử dụng thông tin xuất hiện trong phần Context. Nếu phần Context không chứa câu trả lời cho câu hỏi, bạn PHẢI trả lời chính xác là: "Xin lỗi, tài liệu không đề cập đến thông tin này."
        3. KHÔNG BỊA ĐẶT: Tuyệt đối không được tự suy diễn, không được dùng kiến thức bên ngoài Context để trả lời.

        🚨 QUY TẮC ĐỊNH DẠNG TOÁN HỌC:
        - Nếu có công thức toán học, bạn PHẢI sử dụng LaTeX.
        - Sử dụng cặp dấu $$ cho công thức hiển thị riêng biệt
        - Chỉ Sử dụng cặp dấu $ cho công thức nằm trong dòng văn bản
        - TUYỆT ĐỐI KHÔNG dùng các ký hiệu như \[ \] hoặc \( \).
        """

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )

        self.chain = prompt | self.llm | StrOutputParser()
    
    # Hybrid Search + CrossEncoder Reranking
    def _custom_hybrid_retrieve(self, question: str, top_k_retriever:int = 10, top_k_final:int = 3) -> List[Document]:
        if not self.vector_store or not hasattr(self, 'chunks'):
            return []

        # 1. Vector Search (Lấy 10 ứng viên)
        faiss_docs = self.vector_store.similarity_search(question, k=top_k_retriever)

        # 2. BM25 Keyword Search (Lấy 10 ứng viên)
        tokenized_query = question.lower().split()
        bm25_docs = self.bm25.get_top_n(tokenized_query, self.chunks, n=top_k_retriever)

        # 3. Gộp ứng viên và loại bỏ trùng lặp (Dùng nội dung làm key)
        unique_candidates = {}
        for doc in faiss_docs + bm25_docs:
            unique_candidates[doc.page_content] = doc
        
        candidates = list(unique_candidates.values())

        if not candidates:
            return []

        # 4. Chấm điểm bằng CrossEncoder
        pairs = [[question, doc.page_content] for doc in candidates]
        print(f"Scoring %d candidates with CrossEncoder..." % len(pairs))
        
        
        ce_scores = self.cross_encoder.predict(pairs)

        # 5. Gắn điểm vào metadata và sắp xếp giảm dần
        for i, doc in enumerate(candidates):
            doc.metadata['ce_score'] = float(ce_scores[i])
            
        print("List sau khi chấm điểm (trước khi sort):")
        for doc in candidates:
            print(f"Score: {doc.metadata['ce_score']:.4f} | Content preview: {doc.page_content[:50]}...")

        candidates.sort(key=lambda x: x.metadata['ce_score'], reverse=True)
        
        # 6. Trả về đúng số lượng top_k_final cần thiết
        return candidates[:top_k_final]
    
    def _get_vectorstore_root(self) -> str:
        root = os.path.join(settings.MEDIA_ROOT, "vectorstores")
        os.makedirs(root, exist_ok=True)
        return root

    def _get_vectorstore_dir(self, conversation_id: int) -> str:
        path = os.path.join(self._get_vectorstore_root(), str(conversation_id))
        os.makedirs(path, exist_ok=True)
        return path

    def _get_vectorstore_meta_path(self, conversation_id: int) -> str:
        return os.path.join(self._get_vectorstore_dir(conversation_id), "metadata.json")

    def _save_vectorstore(self, conversation_id: int, source_file_paths: Optional[List[str]] = None):
        """Lưu FAISS, BM25 và Metadata (danh sách files) xuống ổ cứng"""
        if not self.vector_store:
            return

        vector_dir = self._get_vectorstore_dir(conversation_id)
        
        # 1. Lưu FAISS Vector Database
        self.vector_store.save_local(vector_dir)

        chunks_path = os.path.join(vector_dir, "chunks.pkl")
        with open(chunks_path, "wb") as f:
            pickle.dump(self.chunks, f)

        # 3. Chuẩn bị Metadata (Chuyển sang dạng List)
        # Nếu có source paths, ta convert tất cả sang absolute paths
        abs_source_paths = [os.path.abspath(p) for p in source_file_paths] if source_file_paths else []

        
        metadata = {
            "conversation_id": conversation_id,
            "file_names": self.current_file_names,  # Lưu dưới dạng List[str]
            "file_types": self.current_file_types,  # Lưu dưới dạng List[str]
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "source_file_paths": abs_source_paths,  # Lưu dưới dạng List[str]
        }

        # 4. Ghi Metadata ra file JSON
        with open(self._get_vectorstore_meta_path(conversation_id), "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
            
        print(f"✓ Đã lưu thành công Vectorstore và BM25 cho conversation {conversation_id}")
        
    def _load_vectorstore_metadata(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        meta_path = self._get_vectorstore_meta_path(conversation_id)
        if not os.path.exists(meta_path):
            return None
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to read vectorstore metadata: %s", e)
            return None

    def _load_vectorstore_if_compatible(
        self,
        conversation_id: int,
        file_names: Optional[List[str]] = None,
        source_file_paths: Optional[List[str]] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> bool:
        """Kiểm tra điều kiện và khôi phục FAISS + BM25 + Re-ranker"""
        vector_dir = self._get_vectorstore_dir(conversation_id)
        if not os.path.exists(os.path.join(vector_dir, "index.faiss")):
            return False

        metadata = self._load_vectorstore_metadata(conversation_id)
        if not metadata:
            return False

        # --- KIỂM TRA ĐIỀU KIỆN ---
        expected_chunk_size = chunk_size if chunk_size is not None else self.chunk_size
        expected_chunk_overlap = chunk_overlap if chunk_overlap is not None else self.chunk_overlap

        if metadata.get("chunk_size") != expected_chunk_size: return False
        if metadata.get("chunk_overlap") != expected_chunk_overlap: return False

        # Kiểm tra danh sách Tên file (dùng set để bỏ qua thứ tự)
        saved_file_names = metadata.get("file_names", [])
        if file_names and set(saved_file_names) != set(file_names):
            return False

        # Kiểm tra danh sách Đường dẫn file (source paths)
        saved_paths = metadata.get("source_file_paths", [])
        if source_file_paths:
            target_paths = [os.path.abspath(p) for p in source_file_paths]
            if set(saved_paths) != set(target_paths):
                return False
            # Đảm bảo các file nguồn vẫn đang tồn tại trên server (không bị xóa mất)
            for p in target_paths:
                if not os.path.exists(p):
                    return False

        # --- BẮT ĐẦU KHÔI PHỤC (REBUILD PIPELINE) ---
        
        # 1. Khôi phục FAISS (Vector Search)
        self.vector_store = FAISS.load_local(
            vector_dir,
            self.embedding_model,
            allow_dangerous_deserialization=True,
        )


        # 2. Khôi phục BM25 (Keyword Search)
        chunks_path = os.path.join(vector_dir, "chunks.pkl")
        if os.path.exists(chunks_path):
            with open(chunks_path, "rb") as f:
                self.chunks = pickle.load(f)
            # Tái tạo BM25 trong tích tắc
            tokenized_corpus = [doc.page_content.lower().split() for doc in self.chunks]
            self.bm25 = BM25Okapi(tokenized_corpus)

        # 3. Cập nhật trạng thái class & Build Chain
        self.current_file_names = saved_file_names
        self.current_file_types = metadata.get("file_types", [])
        self.current_conversation_id = conversation_id
        
        self._build_chain()
        self.cache.clear()
        self.cache_timestamp.clear()
        
        print(f"✓ Đã load thành công Hybrid Pipeline cho conversation {conversation_id}")
        return True
    
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
        
    def _build_vector_store_from_path(
        self,
        file_path: str,
        file_name: str,
        chunk_size: int,
        chunk_overlap: int,
    ) -> bool:
        file_type = self._get_file_type(file_name)
        print(f"Processing {file_type.upper()}: {file_name}")
        print(f"Chunk config: size={chunk_size}, overlap={chunk_overlap}")

        documents = self._load_document(file_path, file_type)
        if not documents:
            raise ValueError(f"Cannot read content from {file_name}")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = text_splitter.split_documents(documents)
        print(f"Created {len(chunks)} chunks")

        self.vector_store = FAISS.from_documents(chunks, self.embedding_model)
        self.retriever = self.vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 2})
        self._build_chain()

        self.current_file_types = file_type
        self.current_file_names = file_name
        self.cache.clear()
        self.cache_timestamp.clear()
        return True

    def _build_advanced_retriever_from_documents(self, documents: List[Document], chunk_size: int, chunk_overlap: int):
        """Hàm dùng chung để băm tài liệu, tạo FAISS, tạo BM25 và cấu hình Reranker"""
        if not documents:
            raise ValueError("Không có tài liệu nào để xử lý.")

        # 1. Chunking toàn bộ documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = text_splitter.split_documents(documents)
        # Lưu chunks vào class để tái sử dụng cho BM25
        
        chunks = [c for c in chunks if c.page_content.strip()]
        # Kiểm tra xem sau khi cắt và lọc, có còn chunk nào sống sót không
        if not chunks:
            print("⚠ Lỗi: Tài liệu rỗng, không có chữ (Có thể là PDF dạng ảnh/scan)!")
            return False
        # -----------------------------------

        print(f"Created {len(chunks)} chunks từ {len(set(d.metadata.get('source_file', 'unknown') for d in documents))} file.")
        
        self.chunks = chunks 
        self.vector_store = FAISS.from_documents(chunks, self.embedding_model)

        # Khởi tạo BM25
        tokenized_corpus = [doc.page_content.lower().split() for doc in chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

        self._build_chain()
        return True

    def process_multiple_files(self, file_paths: List[str], file_names: List[str]):
        """Hàm xử lý danh sách nhiều file cùng lúc"""
        all_documents = []
        
        for file_path, file_name in zip(file_paths, file_names):
            file_type = self._get_file_type(file_name)
            print(f"Loading {file_type.upper()}: {file_name}")
            try:
                docs = self._load_document(file_path, file_type)
                for doc in docs:
                    doc.metadata['source_file'] = file_name 
                all_documents.extend(docs)
            except Exception as e:
                # Nếu pdfplumber không đọc được file, nó sẽ in ra lỗi ở đây
                print(f"Lỗi khi đọc file {file_name}: {e}")
        
        if not all_documents:
            print("⚠ Lỗi: Không trích xuất được chữ nào từ file này (Có thể là PDF dạng ảnh).")
            return False

        # Băm và tạo retriever
        success =self._build_advanced_retriever_from_documents(
            documents=all_documents, 
            chunk_size=self.chunk_size, 
            chunk_overlap=self.chunk_overlap
        )
        # Nếu build thất bại (do file rỗng), báo False luôn
        if not success:
            return False
        
        # Cập nhật danh sách file đang mở để chuẩn bị lưu Metadata
        self.current_file_names = file_names
        
        return True
    
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

    def process_document_with_config(
        self,
        file,
        file_name: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        conversation_id: Optional[int] = None,
        source_file_path: Optional[str] = None,
    ) -> bool:
        use_chunk_size = chunk_size if chunk_size is not None else self.chunk_size
        use_chunk_overlap = chunk_overlap if chunk_overlap is not None else self.chunk_overlap

        tmp_path = None
        try:
            file_type = self._get_file_type(file_name)
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp_file:
                for chunk in file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name

            self.chunk_size = use_chunk_size
            self.chunk_overlap = use_chunk_overlap
            self._build_vector_store_from_path(tmp_path, file_name, use_chunk_size, use_chunk_overlap)

            if conversation_id is not None:
                self.current_conversation_id = int(conversation_id)
                persisted_source = source_file_path if source_file_path else tmp_path
                self._save_vectorstore(int(conversation_id), persisted_source)
            return True
        except Exception as e:
            print(f"Error processing {file_name}: {e}")
            return False
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def process_document(
        self,
        file,
        file_name: str,
        conversation_id: Optional[int] = None,
        source_file_path: Optional[str] = None,
    ) -> bool:
        return self.process_document_with_config(
            file=file,
            file_name=file_name,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            conversation_id=conversation_id,
            source_file_path=source_file_path,
        )

    def process_pdf(self, pdf_file, conversation_id: Optional[int] = None) -> bool:
        return self.process_document(
            pdf_file,
            getattr(pdf_file, "name", "document.pdf"),
            conversation_id=conversation_id,
        )

    def load_or_create_conversation_index(
        self,
        conversation_id: int,
        file_path: str,
        file_name: str,
        force_reprocess: bool = False,
    ) -> bool:
        conversation_id = int(conversation_id)
        if not force_reprocess:
            loaded = self._load_vectorstore_if_compatible(
                conversation_id=conversation_id,
                file_name=file_name,
                source_file_path=file_path,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )
            if loaded:
                print(f"Loaded persisted vectorstore for conversation {conversation_id}")
                return True

        try:
            self._build_vector_store_from_path(file_path, file_name, self.chunk_size, self.chunk_overlap)
            self.current_conversation_id = conversation_id
            self._save_vectorstore(conversation_id, file_path)
            return True
        except Exception as e:
            print(f"Error loading conversation index: {e}")
            return False

    def clear_persisted_index(self, conversation_id: int):
        vector_dir = os.path.join(self._get_vectorstore_root(), str(conversation_id))
        if os.path.exists(vector_dir):
            shutil.rmtree(vector_dir, ignore_errors=True)

    def ask_question(self, question: str) -> Dict[str, Any]:
        # if not self.chain or not self.retriever:
        #     return {"answer": self._get_quick_answer(question), "sources": []}

        cache_key = question.lower().strip()
        if cache_key in self.cache:
            if time.time() - self.cache_timestamp.get(cache_key, 0) > 1200:
                del self.cache[cache_key]
            else:
                return self.cache[cache_key]

        try:
            # Tự gọi bộ máy Hybrid thủ công
            source_docs = self._custom_hybrid_retrieve(question)
            
            # Gộp text để cung cấp thông tin cho LLM
            if not source_docs:
                context = "Không có thông tin liên quan trong tài liệu."
            else:
                context = "\n\n".join([doc.page_content for doc in source_docs])

            # Truyền thủ công vào chain
            answer = self.chain.invoke({
                "context": context, 
                "question": question
            })

            sources = []
            for doc in source_docs: # Nếu dùng Re-ranking thì có thể lấy top 3 tùy ý
                page_number = doc.metadata.get("page", "?")
                file_type = doc.metadata.get("file_type", "unknown") 
                
                # Lấy tên file gốc mà mình đã gán lúc chunking
                source_file = doc.metadata.get("source_file", "Tài liệu") 

                sources.append(
                    {
                        "content": doc.page_content[:180] + "..." if len(doc.page_content) > 180 else doc.page_content,
                        "page_number": page_number,
                        "file_type": file_type,
                        "source_file": source_file, # Thêm dòng này để truyền tên file ra ngoài
                        "metadata": doc.metadata,
                    }
                )

            result = {"answer": answer, "sources": sources}
            self.cache[cache_key] = result
            self.cache_timestamp[cache_key] = time.time()
            return result

        except Exception as e:
            print(f"Error ask_question: {e}")
            return {"answer": "Khong có câu trả lời", "sources": []}
        

    def _lengthen_answer(self, short_answer: str, question: str) -> str:
        """Thêm nội dung tự nhiên để đủ độ dài"""
        fillers = [
            " Ngoài ra, bạn có thể xem xét thêm rằng ",
            " Trong thực tế, điều này thường được áp dụng như sau: ",
            " Tóm lại, đây là hướng xử lý hợp lý nhất cho trường hợp của bạn.",
            " Điều quan trọng là cần lưu ý thêm một chút về "
        ]
        return short_answer.strip() + random.choice(fillers)
        
    
    def get_document_info(self) -> Dict[str, Any]:
        """Lấy thông tin document hiện tại"""
        return {
            'file_name': self.current_file_names,
            'file_type': self.current_file_types,
            'has_document': self.vector_store is not None
        }

    def clear(self):
        self.vector_store = None
        self.retriever = None
        self.chain = None
        self.cache.clear()
        self.cache_timestamp.clear()
        self.current_file_types = []
        self.current_file_names = []
        print("✓ RAG service đã xóa sạch")

# Singleton
rag_service = RAGService()