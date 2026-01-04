# main.py
# CLI Entry Point cho FuOverflow Scraper v2.0 - Library & Queue System

import argparse
import sys
import os
import requests
from typing import Optional
from database.models import DatabaseManager, ThreadStatus
from library.library_manager import LibraryManager
from queue_system.queue_manager import QueueManager
from queue_system.worker import QueueWorker
from library.thread_utils import normalize_url
import config

def setup_session() -> requests.Session:
    """Thiết lập requests session với cookies"""
    if not config.COOKIES:
        print("(!) Lỗi: Cookie chưa được cấu hình trong file 'config.py'.")
        sys.exit(1)
    
    session = requests.Session()
    session.cookies.update(config.COOKIES)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    return session

def validate_url(url: str) -> bool:
    """Validate URL format"""
    normalized = normalize_url(url)
    return normalized.startswith('http://') or normalized.startswith('https://')

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024
        i += 1
    return f"{size:.2f} {size_names[i]}"

def get_file_size(file_path: str) -> Optional[int]:
    """Get file size in bytes"""
    if not file_path:
        return None
    try:
        abs_path = os.path.join(config.SAVE_DIRECTORY, file_path)
        if os.path.exists(abs_path):
            return os.path.getsize(abs_path)
    except Exception:
        pass
    return None

def main():
    parser = argparse.ArgumentParser(
        description='FuOverflow Exam Scraper - Library & Queue System v2.0'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Command: add
    add_parser = subparsers.add_parser('add', help='Thêm URL vào queue')
    add_parser.add_argument('urls', nargs='+', help='URL(s) của thread(s) cần cào')
    
    # Command: list
    list_parser = subparsers.add_parser('list', help='Liệt kê threads trong library')
    list_parser.add_argument('--status', choices=['pending', 'processing', 'completed', 'failed'], 
                            help='Lọc theo status')
    list_parser.add_argument('--limit', type=int, help='Giới hạn số lượng')
    
    # Command: worker
    worker_parser = subparsers.add_parser('worker', help='Chạy worker để xử lý queue')
    worker_parser.add_argument('--stop-on-empty', action='store_true',
                              help='Dừng worker khi queue rỗng')
    worker_parser.add_argument('--interval', type=int, default=5,
                              help='Thời gian nghỉ giữa các lần check queue (giây)')
    
    # Command: stats
    subparsers.add_parser('stats', help='Xem thống kê queue')
    
    # Command: show
    show_parser = subparsers.add_parser('show', help='Xem chi tiết một thread')
    show_parser.add_argument('thread_id', type=int, help='ID của thread')
    
    # Command: retry
    retry_parser = subparsers.add_parser('retry', help='Retry các thread failed')
    retry_parser.add_argument('--all', action='store_true', help='Retry tất cả failed threads')
    retry_parser.add_argument('--id', type=int, help='Retry thread với ID cụ thể')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Khởi tạo DB và managers
    db_manager = DatabaseManager()
    library_manager = LibraryManager(db_manager)
    queue_manager = QueueManager(db_manager)
    
    # Command: add
    if args.command == 'add':
        session = setup_session()
        
        added_count = 0
        skipped_count = 0
        
        for url in args.urls:
            try:
                # Validate URL
                if not validate_url(url):
                    print(f"✗ URL không hợp lệ: {url}")
                    continue
                
                # Kiểm tra đã có chưa
                existing = library_manager.check_thread_exists(url)
                if existing:
                    if existing.status == ThreadStatus.COMPLETED:
                        print(f"✓ Đã có trong library (completed): {existing.title}")
                        print(f"  URL: {existing.url}")
                        if existing.pdf_path:
                            pdf_size = get_file_size(existing.pdf_path)
                            size_str = f" ({format_file_size(pdf_size)})" if pdf_size else ""
                            print(f"  PDF: {existing.pdf_path}{size_str}")
                    else:
                        print(f"✓ Đã có trong library (status: {existing.status.value}): {existing.title}")
                        print(f"  URL: {existing.url}")
                    skipped_count += 1
                else:
                    # Thêm mới
                    thread = library_manager.add_thread(url)
                    print(f"✓ Đã thêm vào queue: {thread.title}")
                    print(f"  URL: {thread.url}")
                    print(f"  Status: {thread.status.value}")
                    added_count += 1
            except Exception as e:
                print(f"✗ Lỗi khi thêm URL {url}: {e}")
        
        print(f"\n--- Tóm tắt: Đã thêm {added_count}, Bỏ qua {skipped_count} ---")
    
    # Command: list
    elif args.command == 'list':
        status = ThreadStatus(args.status) if args.status else None
        threads = library_manager.get_all_threads(status=status, limit=args.limit)
        
        if not threads:
            print("Không có thread nào trong library.")
            return
        
        print(f"\n{'ID':<6} {'Status':<12} {'Title':<50} {'Created At'}")
        print("-" * 100)
        
        for thread in threads:
            created = thread.created_at.strftime('%Y-%m-%d %H:%M') if thread.created_at else 'N/A'
            title = thread.title[:47] + '...' if len(thread.title) > 50 else thread.title
            print(f"{thread.id:<6} {thread.status.value:<12} {title:<50} {created}")
    
    # Command: worker
    elif args.command == 'worker':
        session = setup_session()
        worker = QueueWorker(db_manager, session)
        worker.sleep_interval = args.interval
        worker.run_loop(stop_on_empty=args.stop_on_empty)
    
    # Command: stats
    elif args.command == 'stats':
        stats = queue_manager.get_queue_stats()
        total = sum(stats.values())
        
        print("\n=== Queue Statistics ===")
        print(f"Total threads: {total}")
        print(f"  - Pending:    {stats['pending']}")
        print(f"  - Processing: {stats['processing']}")
        print(f"  - Completed:  {stats['completed']}")
        print(f"  - Failed:     {stats['failed']}")
        print("=" * 25)
    
    # Command: show
    elif args.command == 'show':
        thread = library_manager.get_thread_by_id(args.thread_id)
        if not thread:
            print(f"✗ Không tìm thấy thread với ID: {args.thread_id}")
            return
        
        print(f"\n{'='*60}")
        print(f"Thread ID: {thread.id}")
        print(f"{'='*60}")
        print(f"Title: {thread.title}")
        print(f"URL: {thread.url}")
        print(f"Status: {thread.status.value}")
        
        if thread.created_at:
            print(f"Created: {thread.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if thread.updated_at:
            print(f"Updated: {thread.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if thread.completed_at:
            print(f"Completed: {thread.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if thread.folder_path:
            print(f"\nFolder: {thread.folder_path}")
            abs_folder = os.path.join(config.SAVE_DIRECTORY, thread.folder_path)
            if os.path.exists(abs_folder):
                file_count = len([f for f in os.listdir(abs_folder) if os.path.isfile(os.path.join(abs_folder, f))])
                print(f"  Files: {file_count}")
        
        if thread.pdf_path:
            pdf_size = get_file_size(thread.pdf_path)
            size_str = f" ({format_file_size(pdf_size)})" if pdf_size else ""
            print(f"PDF: {thread.pdf_path}{size_str}")
        
        if thread.total_questions > 0:
            print(f"Questions: {thread.total_questions}")
        
        if thread.error_message:
            print(f"\nError: {thread.error_message}")
        
        # Show media items count
        media_items = db_manager.get_media_items_by_thread(thread.id)
        if media_items:
            print(f"\nMedia Items: {len(media_items)}")
        
        print(f"{'='*60}\n")
    
    # Command: retry
    elif args.command == 'retry':
        if args.all:
            # Retry all failed threads
            failed_threads = library_manager.get_all_threads(status=ThreadStatus.FAILED)
            if not failed_threads:
                print("Không có thread nào ở trạng thái 'failed'.")
                return
            
            print(f"\nTìm thấy {len(failed_threads)} failed thread(s).")
            retry_count = 0
            for thread in failed_threads:
                thread.status = ThreadStatus.PENDING
                thread.error_message = None
                library_manager.update_thread(thread)
                print(f"✓ Đã reset thread ID {thread.id}: {thread.title}")
                retry_count += 1
            
            print(f"\n--- Đã reset {retry_count} thread(s) về pending ---")
            print("Chạy worker để xử lý lại: python main.py worker")
        
        elif args.id:
            # Retry specific thread
            thread = library_manager.get_thread_by_id(args.id)
            if not thread:
                print(f"✗ Không tìm thấy thread với ID: {args.id}")
                return
            
            if thread.status != ThreadStatus.FAILED:
                print(f"✗ Thread ID {args.id} không ở trạng thái 'failed'. Status hiện tại: {thread.status.value}")
                return
            
            thread.status = ThreadStatus.PENDING
            thread.error_message = None
            library_manager.update_thread(thread)
            print(f"✓ Đã reset thread ID {args.id} về pending: {thread.title}")
            print("Chạy worker để xử lý lại: python main.py worker")
        
        else:
            print("(!) Cần chỉ định --all hoặc --id <thread_id>")
            print("    Ví dụ: python main.py retry --all")
            print("    Ví dụ: python main.py retry --id 1")

if __name__ == "__main__":
    main()

