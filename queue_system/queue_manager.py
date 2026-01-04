# queue/queue_manager.py

from typing import Optional, Dict
from datetime import datetime
from database.models import DatabaseManager, Thread, ThreadStatus
from library.library_manager import LibraryManager

class QueueManager:
    """Quản lý queue (hàng chờ xử lý threads)"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Khởi tạo QueueManager.
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
        self.library = LibraryManager(db_manager)
    
    def get_next_pending(self) -> Optional[Thread]:
        """
        Lấy thread pending cũ nhất (FIFO - First In First Out).
        
        Returns:
            Thread object nếu có, None nếu không có thread nào pending
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM threads 
                WHERE status = ? 
                ORDER BY created_at ASC 
                LIMIT 1
            """, (ThreadStatus.PENDING.value,))
            row = cursor.fetchone()
            
            if row:
                return self.db.thread_from_row(row)
            return None
    
    def update_thread_status(
        self, 
        thread_id: int, 
        status: ThreadStatus,
        error_message: Optional[str] = None,
        folder_path: Optional[str] = None,
        pdf_path: Optional[str] = None,
        total_questions: int = 0
    ):
        """
        Cập nhật status và thông tin của thread.
        
        Args:
            thread_id: ID của thread
            status: Status mới
            error_message: Thông báo lỗi (nếu có)
            folder_path: Đường dẫn thư mục (relative path)
            pdf_path: Đường dẫn file PDF (relative path)
            total_questions: Tổng số câu hỏi
        """
        thread = self.library.get_thread_by_id(thread_id)
        if not thread:
            return
        
        thread.status = status
        thread.updated_at = datetime.now()
        thread.error_message = error_message
        
        if folder_path is not None:
            thread.folder_path = folder_path
        if pdf_path is not None:
            thread.pdf_path = pdf_path
        if total_questions > 0:
            thread.total_questions = total_questions
        
        if status == ThreadStatus.COMPLETED or status == ThreadStatus.FAILED:
            thread.completed_at = datetime.now()
        
        self.library.update_thread(thread)
    
    def get_queue_stats(self) -> Dict[str, int]:
        """
        Lấy thống kê queue (số lượng threads theo từng status).
        
        Returns:
            Dict với keys: 'pending', 'processing', 'completed', 'failed'
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status, COUNT(*) 
                FROM threads 
                GROUP BY status
            """)
            results = cursor.fetchall()
            
            stats = {
                'pending': 0,
                'processing': 0,
                'completed': 0,
                'failed': 0
            }
            
            for status, count in results:
                stats[status] = count
            
            return stats


