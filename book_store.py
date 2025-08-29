from typing import Dict, List
from datetime import datetime
import threading
import json
import os
import logging
from pathlib import Path

from models import Book, BookCreate, BookUpdate, BookStatus
from exceptions import GameTrackerException

logger = logging.getLogger(__name__)

class BookNotFoundError(GameTrackerException):
    """书籍未找到异常"""
    def __init__(self, book_id: int):
        super().__init__(f"Book with ID {book_id} not found")

class BookLimitExceededError(GameTrackerException):
    """书籍数量限制异常"""
    def __init__(self, limit: int):
        super().__init__(f"Cannot exceed reading limit of {limit} books")

class DuplicateBookError(GameTrackerException):
    """重复书籍异常"""
    def __init__(self, title: str):
        super().__init__(f"A book with title '{title}' is already being read")

class BookStore:
    def __init__(self, default_limit: int = 3, data_file: str = "books_data.json"):
        self._books: Dict[int, Book] = {}
        self._next_id = 1
        self._limit = default_limit
        self._lock = threading.Lock()
        self._data_file = Path(data_file)
        
        self._load_data()
    
    def get_all_books(self) -> dict:
        """Get all books grouped by status"""
        with self._lock:
            reading = [book for book in self._books.values() if book.status == BookStatus.READING]
            paused = [book for book in self._books.values() if book.status == BookStatus.PAUSED]
            reference = [book for book in self._books.values() if book.status == BookStatus.REFERENCE]
            planned = [book for book in self._books.values() if book.status == BookStatus.PLANNED]
            finished = [book for book in self._books.values() if book.status == BookStatus.FINISHED]
            dropped = [book for book in self._books.values() if book.status == BookStatus.DROPPED]
            
            return {
                "reading": sorted(reading, key=lambda b: b.created_at, reverse=True),
                "paused": sorted(paused, key=lambda b: b.created_at, reverse=True),
                "reference": sorted(reference, key=lambda b: b.created_at, reverse=True),
                "planned": sorted(planned, key=lambda b: b.created_at, reverse=True),
                "finished": sorted(finished, key=lambda b: b.ended_at or b.created_at, reverse=True),
                "dropped": sorted(dropped, key=lambda b: b.ended_at or b.created_at, reverse=True)
            }
    
    def get_reading_count(self) -> dict:
        """Get current reading book count and limit"""
        with self._lock:
            reading_count = len([book for book in self._books.values() if book.status == BookStatus.READING])
            paused_count = len([book for book in self._books.values() if book.status == BookStatus.PAUSED])
            reference_count = len([book for book in self._books.values() if book.status == BookStatus.REFERENCE])
            planned_count = len([book for book in self._books.values() if book.status == BookStatus.PLANNED])
            
            return {
                "count": reading_count,
                "limit": self._limit,
                "paused_count": paused_count,
                "reference_count": reference_count,
                "planned_count": planned_count
            }
    
    def add_book(self, book_data: BookCreate) -> Book:
        """Add a new book"""
        with self._lock:
            # 检查是否超出阅读限制（仅对正在阅读的书籍限制）
            if book_data.status == BookStatus.READING:
                reading_count = len([b for b in self._books.values() if b.status == BookStatus.READING])
                if reading_count >= self._limit:
                    raise BookLimitExceededError(self._limit)
                
                # 检查是否已有相同书名的正在阅读的书籍
                for book in self._books.values():
                    if book.status == BookStatus.READING and book.title.strip().lower() == book_data.title.strip().lower():
                        raise DuplicateBookError(book_data.title)
            
            # 创建新书籍
            book = Book(
                id=self._next_id,
                user_id=1,  # JSON模式下的默认用户ID
                title=book_data.title.strip(),
                author=book_data.author.strip(),
                status=book_data.status,
                notes=book_data.notes,
                rating=book_data.rating,
                reason=book_data.reason,
                progress=book_data.progress or "",
                created_at=datetime.now()
            )
            
            # 如果是已读完或已弃读，设置结束时间
            if book.status in [BookStatus.FINISHED, BookStatus.DROPPED]:
                book.ended_at = datetime.now()
            
            self._books[self._next_id] = book
            self._next_id += 1
            
            self._save_data()
            return book
    
    def update_book(self, book_id: int, updates: BookUpdate) -> Book:
        """Update an existing book"""
        with self._lock:
            if book_id not in self._books:
                raise BookNotFoundError(book_id)
            
            book = self._books[book_id]
            old_status = book.status
            
            # 应用更新
            update_data = updates.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(book, field):
                    setattr(book, field, value)
            
            # 状态变化处理
            if "status" in update_data:
                new_status = updates.status
                
                # 如果状态改为正在阅读，检查限制
                if new_status == BookStatus.READING and old_status != BookStatus.READING:
                    reading_count = len([b for b in self._books.values() 
                                       if b.status == BookStatus.READING and b.id != book_id])
                    if reading_count >= self._limit:
                        raise BookLimitExceededError(self._limit)
                    
                    # 检查重复书名
                    if "title" not in update_data:  # 如果没有同时更新书名
                        for other_book in self._books.values():
                            if (other_book.id != book_id and 
                                other_book.status == BookStatus.READING and 
                                other_book.title.strip().lower() == book.title.strip().lower()):
                                raise DuplicateBookError(book.title)
                
                # 状态变为已读完或已弃读时，设置结束时间
                if new_status in [BookStatus.FINISHED, BookStatus.DROPPED] and old_status not in [BookStatus.FINISHED, BookStatus.DROPPED]:
                    book.ended_at = datetime.now()
                # 状态从已读完或已弃读变为其他状态时，清除结束时间
                elif old_status in [BookStatus.FINISHED, BookStatus.DROPPED] and new_status not in [BookStatus.FINISHED, BookStatus.DROPPED]:
                    book.ended_at = None
            
            # 检查书名重复（如果同时更新了书名和状态为正在阅读）
            if "title" in update_data and book.status == BookStatus.READING:
                for other_book in self._books.values():
                    if (other_book.id != book_id and 
                        other_book.status == BookStatus.READING and 
                        other_book.title.strip().lower() == book.title.strip().lower()):
                        raise DuplicateBookError(book.title)
            
            self._save_data()
            return book
    
    def delete_book(self, book_id: int) -> bool:
        """Delete a book"""
        with self._lock:
            if book_id not in self._books:
                raise BookNotFoundError(book_id)
            
            del self._books[book_id]
            self._save_data()
            return True
    
    def update_limit(self, new_limit: int) -> dict:
        """Update the reading limit"""
        with self._lock:
            if new_limit < 1:
                raise ValueError("Limit must be at least 1")
            
            self._limit = new_limit
            self._save_data()
            
            # 直接在锁内计算统计数据，避免死锁
            reading_count = len([book for book in self._books.values() if book.status == BookStatus.READING])
            paused_count = len([book for book in self._books.values() if book.status == BookStatus.PAUSED])
            reference_count = len([book for book in self._books.values() if book.status == BookStatus.REFERENCE])
            planned_count = len([book for book in self._books.values() if book.status == BookStatus.PLANNED])
            
            return {
                "count": reading_count,
                "limit": self._limit,
                "paused_count": paused_count,
                "reference_count": reference_count,
                "planned_count": planned_count
            }
    
    def _load_data(self):
        """Load data from JSON file"""
        try:
            if self._data_file.exists():
                with open(self._data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    self._next_id = data.get("next_id", 1)
                    self._limit = data.get("limit", self._limit)
                    
                    # Load books
                    for book_data in data.get("books", {}).values():
                        # 为JSON模式提供默认user_id
                        if 'user_id' not in book_data:
                            book_data['user_id'] = 1
                        book = Book(**book_data)
                        self._books[book.id] = book
                        
                    logger.info(f"Loaded {len(self._books)} books from {self._data_file}")
            else:
                logger.info(f"No existing data file found at {self._data_file}, starting with empty book list")
                self._save_data()  # Create initial file
                
        except Exception as e:
            logger.error(f"Error loading book data: {e}")
            # Continue with empty data
    
    def _save_data(self):
        """Save data to JSON file"""
        try:
            data = {
                "books": {
                    str(book.id): book.dict() for book in self._books.values()
                },
                "next_id": self._next_id,
                "limit": self._limit
            }
            
            # 创建目录（如果不存在）
            self._data_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入临时文件然后重命名，确保原子性
            temp_file = self._data_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            temp_file.replace(self._data_file)
            logger.debug(f"Book data saved to {self._data_file}")
            
        except Exception as e:
            logger.error(f"Error saving book data: {e}")
            raise