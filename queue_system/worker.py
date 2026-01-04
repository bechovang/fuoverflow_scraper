# queue_system/worker.py

import time
import requests
from typing import Optional
from database.models import DatabaseManager, ThreadStatus
from queue_system.queue_manager import QueueManager
from scraper.scraper import download_images_with_comments_from_thread
import config

class QueueWorker:
    """Background worker để xử lý queue threads"""
    
    def __init__(self, db_manager: DatabaseManager, session: requests.Session):
        """
        Khởi tạo QueueWorker.
        
        Args:
            db_manager: DatabaseManager instance
            session: requests.Session với cookies đã được setup
        """
        self.db = db_manager
        self.session = session
        self.queue_manager = QueueManager(db_manager)
        self.is_running = False
        self.sleep_interval = 5  # Giây giữa các lần check queue
    
    def process_queue_once(self) -> bool:
        """
        Xử lý một thread trong queue.
        
        Returns:
            True nếu có thread được xử lý, False nếu queue rỗng
        """
        thread = self.queue_manager.get_next_pending()
        
        if not thread:
            return False
        
        try:
            # Update status = processing
            self.queue_manager.update_thread_status(thread.id, ThreadStatus.PROCESSING)
            
            print(f"\n{'='*60}")
            print(f"[WORKER] Xử lý thread: {thread.title}")
            print(f"[WORKER] URL: {thread.url}")
            print(f"[WORKER] ID: {thread.id}")
            print(f"{'='*60}")
            
            # Chuẩn bị thread_info dict cho hàm scraper
            thread_info = {
                'url': thread.url,
                'title': thread.title
            }
            
            # Gọi hàm scrape (refactored, return dict)
            result = download_images_with_comments_from_thread(self.session, thread_info, thread.id)
            
            if result['success']:
                # Lưu media items vào DB
                if result.get('media_items_data'):
                    self.db.save_media_items(thread.id, result['media_items_data'])
                
                # Update thread status = completed
                self.queue_manager.update_thread_status(
                    thread.id,
                    ThreadStatus.COMPLETED,
                    folder_path=result['folder_path'],
                    pdf_path=result['pdf_path'],
                    total_questions=result['total_questions']
                )
                
                print(f"\n[WORKER] ✓ Hoàn thành: {thread.title}")
                print(f"[WORKER]   - Câu hỏi: {result['total_questions']}")
                print(f"[WORKER]   - Folder: {result['folder_path']}")
                if result['pdf_path']:
                    print(f"[WORKER]   - PDF: {result['pdf_path']}")
            else:
                # Update status = failed
                error_msg = result.get('error', 'Unknown error')
                self.queue_manager.update_thread_status(
                    thread.id,
                    ThreadStatus.FAILED,
                    error_message=error_msg
                )
                
                print(f"\n[WORKER] ✗ Thất bại: {thread.title}")
                print(f"[WORKER]   Lỗi: {error_msg}")
            
            return True
            
        except Exception as e:
            # Update status = failed
            self.queue_manager.update_thread_status(
                thread.id,
                ThreadStatus.FAILED,
                error_message=str(e)
            )
            
            print(f"\n[WORKER] ✗ Exception: {e}")
            return True  # Đã xử lý (dù thất bại)
    
    def run_loop(self, stop_on_empty: bool = False):
        """
        Chạy worker loop liên tục.
        
        Args:
            stop_on_empty: Nếu True, dừng khi queue rỗng. Nếu False, loop mãi mãi.
        """
        self.is_running = True
        
        print(f"\n{'='*60}")
        print(f"[WORKER] Bắt đầu worker loop")
        print(f"[WORKER] Sleep interval: {self.sleep_interval}s")
        print(f"[WORKER] Stop on empty: {stop_on_empty}")
        print(f"{'='*60}\n")
        
        try:
            while self.is_running:
                stats = self.queue_manager.get_queue_stats()
                pending_count = stats.get('pending', 0)
                
                if pending_count == 0:
                    if stop_on_empty:
                        print("\n[WORKER] Queue rỗng. Dừng worker.")
                        break
                    else:
                        print(f"\n[WORKER] Queue rỗng. Đợi {self.sleep_interval}s...")
                        time.sleep(self.sleep_interval)
                        continue
                
                print(f"\n[WORKER] Queue stats: {stats}")
                
                # Xử lý một thread
                processed = self.process_queue_once()
                
                if not processed:
                    # Không có thread nào, nghỉ một chút
                    time.sleep(self.sleep_interval)
                
        except KeyboardInterrupt:
            print("\n[WORKER] Nhận tín hiệu dừng (Ctrl+C). Dừng worker...")
            self.is_running = False
        except Exception as e:
            print(f"\n[WORKER] Lỗi trong worker loop: {e}")
            self.is_running = False
        
        print("\n[WORKER] Worker đã dừng.")
    
    def stop(self):
        """Dừng worker"""
        self.is_running = False

