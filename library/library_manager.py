# library/library_manager.py

from typing import Optional, List
from datetime import datetime
from database.models import DatabaseManager, Thread, ThreadStatus
from library.thread_utils import normalize_url

class LibraryManager:
    """Quản lý library (thư viện threads)"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Khởi tạo LibraryManager.
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
    
    def check_thread_exists(self, url: str) -> Optional[Thread]:
        """
        Kiểm tra thread đã có trong library chưa.
        
        Args:
            url: URL của thread
        
        Returns:
            Thread object nếu có, None nếu chưa có
        """
        normalized_url = normalize_url(url)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM threads WHERE url = ?", (normalized_url,))
            row = cursor.fetchone()
            
            if row:
                return self.db.thread_from_row(row)
            return None
    
    def add_thread(self, url: str, title: str = None) -> Thread:
        """
        Thêm thread vào library (với status = pending).
        Nếu đã tồn tại, return thread hiện có.
        
        Args:
            url: URL của thread
            title: Tiêu đề của thread (nếu không có sẽ dùng URL)
        
        Returns:
            Thread object
        """
        normalized_url = normalize_url(url)
        
        # Kiểm tra đã có chưa
        existing = self.check_thread_exists(normalized_url)
        if existing:
            return existing
        
        # Thêm mới
        if not title:
            # Fallback title từ URL
            title = normalized_url.split('/')[-1]
            if not title or title == normalized_url:
                title = normalized_url
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO threads (url, title, status)
                VALUES (?, ?, ?)
            """, (normalized_url, title, ThreadStatus.PENDING.value))
            conn.commit()
            
            thread_id = cursor.lastrowid
            cursor.execute("SELECT * FROM threads WHERE id = ?", (thread_id,))
            row = cursor.fetchone()
            return self.db.thread_from_row(row)
    
    def get_thread_by_id(self, thread_id: int) -> Optional[Thread]:
        """
        Lấy thread theo ID.
        
        Args:
            thread_id: ID của thread
        
        Returns:
            Thread object nếu có, None nếu không tìm thấy
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM threads WHERE id = ?", (thread_id,))
            row = cursor.fetchone()
            
            if row:
                return self.db.thread_from_row(row)
            return None
    
    def get_all_threads(
        self, 
        status: Optional[ThreadStatus] = None, 
        limit: Optional[int] = None
    ) -> List[Thread]:
        """
        Lấy danh sách threads, có thể filter theo status.
        
        Args:
            status: Filter theo status (None = lấy tất cả)
            limit: Giới hạn số lượng (None = không giới hạn)
        
        Returns:
            List các Thread objects, sắp xếp theo created_at DESC (mới nhất trước)
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if status:
                query = "SELECT * FROM threads WHERE status = ? ORDER BY created_at DESC"
                params = (status.value,)
            else:
                query = "SELECT * FROM threads ORDER BY created_at DESC"
                params = ()
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [self.db.thread_from_row(row) for row in rows]
    
    def update_thread(self, thread: Thread):
        """
        Cập nhật thông tin thread trong database.
        
        Args:
            thread: Thread object cần cập nhật
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE threads 
                SET title = ?, status = ?, folder_path = ?, pdf_path = ?,
                    total_questions = ?, updated_at = CURRENT_TIMESTAMP,
                    completed_at = ?, error_message = ?
                WHERE id = ?
            """, (
                thread.title,
                thread.status.value,
                thread.folder_path,
                thread.pdf_path,
                thread.total_questions,
                thread.completed_at.isoformat() if thread.completed_at else None,
                thread.error_message,
                thread.id
            ))
            conn.commit()


