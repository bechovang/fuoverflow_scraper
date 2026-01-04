# database/models.py

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass
from enum import Enum

class ThreadStatus(Enum):
    """Trạng thái của thread trong queue"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Thread:
    """Model đại diện cho một thread (đề thi)"""
    id: Optional[int]
    url: str
    title: str
    status: ThreadStatus
    folder_path: Optional[str] = None
    pdf_path: Optional[str] = None
    total_questions: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

@dataclass
class MediaItem:
    """Model đại diện cho một media item (câu hỏi)"""
    id: Optional[int]
    thread_id: int
    media_id: str
    filename: Optional[str] = None
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    title: Optional[str] = None
    comments_json: Optional[str] = None
    question_order: int = 0

class DatabaseManager:
    """Quản lý database SQLite cho FuOverflow Scraper"""
    
    def __init__(self, db_path: str = "fuoverflow.db"):
        """
        Khởi tạo DatabaseManager.
        
        Args:
            db_path: Đường dẫn đến file database SQLite
        """
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Tạo connection đến SQLite database"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Khởi tạo database và các bảng nếu chưa có"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Bảng threads
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS threads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    folder_path TEXT,
                    pdf_path TEXT,
                    total_questions INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT
                )
            """)
            
            # Bảng media_items
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS media_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id INTEGER NOT NULL,
                    media_id TEXT NOT NULL,
                    filename TEXT,
                    image_path TEXT,
                    image_url TEXT,
                    title TEXT,
                    comments_json TEXT,
                    question_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (thread_id) REFERENCES threads(id) ON DELETE CASCADE,
                    UNIQUE(thread_id, media_id)
                )
            """)
            
            # Indexes để tăng tốc độ query
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_threads_url ON threads(url)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_threads_status ON threads(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_items_thread ON media_items(thread_id)")
            
            conn.commit()
    
    def thread_from_row(self, row: tuple) -> Thread:
        """
        Chuyển đổi row từ DB thành Thread object.
        
        Args:
            row: Tuple từ cursor.fetchone() hoặc fetchall()
        
        Returns:
            Thread object
        """
        return Thread(
            id=row[0],
            url=row[1],
            title=row[2],
            status=ThreadStatus(row[3]),
            folder_path=row[4],
            pdf_path=row[5],
            total_questions=row[6],
            created_at=datetime.fromisoformat(row[7]) if row[7] else None,
            updated_at=datetime.fromisoformat(row[8]) if row[8] else None,
            completed_at=datetime.fromisoformat(row[9]) if row[9] else None,
            error_message=row[10]
        )
    
    def media_item_from_row(self, row: tuple) -> MediaItem:
        """
        Chuyển đổi row từ DB thành MediaItem object.
        
        Args:
            row: Tuple từ cursor.fetchone() hoặc fetchall()
        
        Returns:
            MediaItem object
        """
        return MediaItem(
            id=row[0],
            thread_id=row[1],
            media_id=row[2],
            filename=row[3],
            image_path=row[4],
            image_url=row[5],
            title=row[6],
            comments_json=row[7],
            question_order=row[8]
        )
    
    def save_media_items(self, thread_id: int, media_items_data: List[Dict]):
        """
        Lưu danh sách media items vào DB.
        
        Args:
            thread_id: ID của thread
            media_items_data: List các dict chứa thông tin media item
                Format: [{
                    'media_id': '117803',
                    'filename': 'q1.webp',
                    'image_path': 'downloaded_images/.../q1.webp',
                    'image_url': 'https://...',
                    'title': 'Q1',
                    'comments': ['A', 'B'],  # List comments
                    'question_order': 1
                }, ...]
        """
        import json
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Xóa media items cũ của thread này (nếu có) để tránh duplicate
            cursor.execute("DELETE FROM media_items WHERE thread_id = ?", (thread_id,))
            
            # Insert media items mới
            for item in media_items_data:
                comments_json = json.dumps(item.get('comments', []), ensure_ascii=False)
                
                cursor.execute("""
                    INSERT INTO media_items 
                    (thread_id, media_id, filename, image_path, image_url, title, comments_json, question_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    thread_id,
                    str(item['media_id']),
                    item.get('filename'),
                    item.get('image_path'),
                    item.get('image_url'),
                    item.get('title'),
                    comments_json,
                    item.get('question_order', 0)
                ))
            
            conn.commit()
    
    def get_media_items_by_thread(self, thread_id: int) -> List[MediaItem]:
        """
        Lấy tất cả media items của một thread.
        
        Args:
            thread_id: ID của thread
        
        Returns:
            List các MediaItem objects, sắp xếp theo question_order
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM media_items 
                WHERE thread_id = ? 
                ORDER BY question_order ASC
            """, (thread_id,))
            rows = cursor.fetchall()
            
            return [self.media_item_from_row(row) for row in rows]


