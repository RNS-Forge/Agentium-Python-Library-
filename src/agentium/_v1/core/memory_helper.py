"""
Memory Helper Module - Context storage & retrieval

This module provides memory and context management capabilities
for maintaining state and context across agent interactions.
"""

import json
import pickle
import sqlite3
import redis
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import hashlib
import threading
from pathlib import Path

from ..utils.logger_utils import LoggerUtils


class StorageBackend(Enum):
    """Storage backend types"""
    MEMORY = "memory"
    SQLITE = "sqlite"
    REDIS = "redis"
    FILE = "file"


class ContextScope(Enum):
    """Context scope levels"""
    SESSION = "session"
    USER = "user"
    GLOBAL = "global"
    TEMPORARY = "temporary"


@dataclass
class MemoryEntry:
    """Memory entry structure"""
    key: str
    value: Any
    scope: ContextScope
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None


@dataclass
class MemoryConfig:
    """Configuration for memory management"""
    backend: StorageBackend = StorageBackend.MEMORY
    connection_string: Optional[str] = None
    default_ttl: Optional[int] = 3600  # 1 hour in seconds
    max_memory_size: int = 100 * 1024 * 1024  # 100MB
    cleanup_interval: int = 300  # 5 minutes
    compression: bool = True
    encryption: bool = False


class MemoryHelper:
    """
    Advanced memory and context management system.
    
    Features:
    - Multiple storage backends
    - Scoped context management
    - TTL support
    - Compression and encryption
    - Search and retrieval
    - Memory optimization
    - Context inheritance
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self.logger = LoggerUtils.get_logger(__name__)
        self._lock = threading.RLock()
        self._memory_store: Dict[str, MemoryEntry] = {}
        self._setup_backend()
        self._setup_cleanup_timer()
    
    def _setup_backend(self):
        """Setup storage backend"""
        if self.config.backend == StorageBackend.SQLITE:
            self._setup_sqlite()
        elif self.config.backend == StorageBackend.REDIS:
            self._setup_redis()
        elif self.config.backend == StorageBackend.FILE:
            self._setup_file_backend()
        # MEMORY backend uses in-memory dictionary (default)
    
    def _setup_sqlite(self):
        """Setup SQLite backend"""
        db_path = self.config.connection_string or "agentium_memory.db"
        self.sqlite_conn = sqlite3.connect(db_path, check_same_thread=False)
        
        # Create table
        self.sqlite_conn.execute('''
            CREATE TABLE IF NOT EXISTS memory_entries (
                key TEXT PRIMARY KEY,
                value BLOB,
                scope TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                expires_at TIMESTAMP,
                metadata TEXT,
                access_count INTEGER,
                last_accessed TIMESTAMP
            )
        ''')
        self.sqlite_conn.commit()
        
        self.logger.info(f"SQLite backend initialized: {db_path}")
    
    def _setup_redis(self):
        """Setup Redis backend"""
        if not redis:
            raise ImportError("Redis library not available")
        
        # Parse connection string or use defaults
        if self.config.connection_string:
            # Simple parsing for redis://host:port/db format
            if self.config.connection_string.startswith('redis://'):
                self.redis_client = redis.from_url(self.config.connection_string)
            else:
                self.redis_client = redis.Redis.from_url(self.config.connection_string)
        else:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        
        # Test connection
        try:
            self.redis_client.ping()
            self.logger.info("Redis backend initialized")
        except redis.ConnectionError as e:
            self.logger.error(f"Redis connection failed: {str(e)}")
            raise
    
    def _setup_file_backend(self):
        """Setup file-based backend"""
        self.file_backend_dir = Path(self.config.connection_string or "agentium_memory")
        self.file_backend_dir.mkdir(exist_ok=True)
        self.logger.info(f"File backend initialized: {self.file_backend_dir}")
    
    def _setup_cleanup_timer(self):
        """Setup periodic cleanup timer"""
        import threading
        
        def cleanup_expired():
            while True:
                try:
                    self.cleanup_expired()
                    threading.Event().wait(self.config.cleanup_interval)
                except Exception as e:
                    self.logger.error(f"Cleanup error: {str(e)}")
        
        cleanup_thread = threading.Thread(target=cleanup_expired, daemon=True)
        cleanup_thread.start()
    
    @LoggerUtils.log_operation("store_memory")
    def store(self, key: str, value: Any, scope: ContextScope = ContextScope.SESSION, 
             ttl: Optional[int] = None, metadata: Optional[Dict] = None) -> bool:
        """
        Store value in memory
        
        Args:
            key: Memory key
            value: Value to store
            scope: Context scope
            ttl: Time to live in seconds
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        with self._lock:
            now = datetime.now()
            expires_at = now + timedelta(seconds=ttl) if ttl else None
            
            entry = MemoryEntry(
                key=key,
                value=value,
                scope=scope,
                created_at=now,
                updated_at=now,
                expires_at=expires_at,
                metadata=metadata or {},
                access_count=0,
                last_accessed=None
            )
            
            try:
                if self.config.backend == StorageBackend.MEMORY:
                    self._memory_store[key] = entry
                elif self.config.backend == StorageBackend.SQLITE:
                    self._store_sqlite(entry)
                elif self.config.backend == StorageBackend.REDIS:
                    self._store_redis(entry)
                elif self.config.backend == StorageBackend.FILE:
                    self._store_file(entry)
                
                self.logger.debug(f"Stored memory entry: {key}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to store memory entry {key}: {str(e)}")
                return False
    
    def retrieve(self, key: str, default: Any = None) -> Any:
        """
        Retrieve value from memory
        
        Args:
            key: Memory key
            default: Default value if key not found
            
        Returns:
            Retrieved value or default
        """
        with self._lock:
            try:
                if self.config.backend == StorageBackend.MEMORY:
                    entry = self._memory_store.get(key)
                elif self.config.backend == StorageBackend.SQLITE:
                    entry = self._retrieve_sqlite(key)
                elif self.config.backend == StorageBackend.REDIS:
                    entry = self._retrieve_redis(key)
                elif self.config.backend == StorageBackend.FILE:
                    entry = self._retrieve_file(key)
                else:
                    entry = None
                
                if entry is None:
                    return default
                
                # Check expiration
                if entry.expires_at and datetime.now() > entry.expires_at:
                    self.delete(key)
                    return default
                
                # Update access statistics
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                
                # Update in storage
                if self.config.backend != StorageBackend.MEMORY:
                    self._update_access_stats(key, entry)
                
                return entry.value
                
            except Exception as e:
                self.logger.error(f"Failed to retrieve memory entry {key}: {str(e)}")
                return default
    
    def delete(self, key: str) -> bool:
        """Delete memory entry"""
        with self._lock:
            try:
                if self.config.backend == StorageBackend.MEMORY:
                    self._memory_store.pop(key, None)
                elif self.config.backend == StorageBackend.SQLITE:
                    self.sqlite_conn.execute("DELETE FROM memory_entries WHERE key = ?", (key,))
                    self.sqlite_conn.commit()
                elif self.config.backend == StorageBackend.REDIS:
                    self.redis_client.delete(f"agentium:memory:{key}")
                elif self.config.backend == StorageBackend.FILE:
                    file_path = self.file_backend_dir / f"{self._hash_key(key)}.pkl"
                    if file_path.exists():
                        file_path.unlink()
                
                self.logger.debug(f"Deleted memory entry: {key}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to delete memory entry {key}: {str(e)}")
                return False
    
    def exists(self, key: str) -> bool:
        """Check if memory entry exists"""
        try:
            value = self.retrieve(key, sentinel=object())
            return value is not sentinel
        except:
            return False
    
    def update(self, key: str, value: Any, metadata: Optional[Dict] = None) -> bool:
        """Update existing memory entry"""
        with self._lock:
            if not self.exists(key):
                return False
            
            try:
                if self.config.backend == StorageBackend.MEMORY:
                    entry = self._memory_store[key]
                    entry.value = value
                    entry.updated_at = datetime.now()
                    if metadata:
                        entry.metadata.update(metadata)
                elif self.config.backend == StorageBackend.SQLITE:
                    # Implementation for other backends
                    pass
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to update memory entry {key}: {str(e)}")
                return False
    
    def search(self, pattern: str, scope: Optional[ContextScope] = None) -> List[str]:
        """Search for keys matching pattern"""
        matching_keys = []
        
        try:
            if self.config.backend == StorageBackend.MEMORY:
                for key, entry in self._memory_store.items():
                    if (pattern in key and 
                        (scope is None or entry.scope == scope)):
                        matching_keys.append(key)
            elif self.config.backend == StorageBackend.SQLITE:
                query = "SELECT key FROM memory_entries WHERE key LIKE ?"
                params = [f"%{pattern}%"]
                
                if scope:
                    query += " AND scope = ?"
                    params.append(scope.value)
                
                cursor = self.sqlite_conn.execute(query, params)
                matching_keys = [row[0] for row in cursor.fetchall()]
            
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
        
        return matching_keys
    
    def list_keys(self, scope: Optional[ContextScope] = None) -> List[str]:
        """List all keys in specified scope"""
        keys = []
        
        try:
            if self.config.backend == StorageBackend.MEMORY:
                for key, entry in self._memory_store.items():
                    if scope is None or entry.scope == scope:
                        keys.append(key)
            elif self.config.backend == StorageBackend.SQLITE:
                if scope:
                    cursor = self.sqlite_conn.execute(
                        "SELECT key FROM memory_entries WHERE scope = ?", (scope.value,))
                else:
                    cursor = self.sqlite_conn.execute("SELECT key FROM memory_entries")
                keys = [row[0] for row in cursor.fetchall()]
            
        except Exception as e:
            self.logger.error(f"Failed to list keys: {str(e)}")
        
        return keys
    
    def clear_scope(self, scope: ContextScope) -> int:
        """Clear all entries in specified scope"""
        cleared_count = 0
        
        with self._lock:
            try:
                if self.config.backend == StorageBackend.MEMORY:
                    keys_to_remove = [
                        key for key, entry in self._memory_store.items()
                        if entry.scope == scope
                    ]
                    for key in keys_to_remove:
                        del self._memory_store[key]
                    cleared_count = len(keys_to_remove)
                
                elif self.config.backend == StorageBackend.SQLITE:
                    cursor = self.sqlite_conn.execute(
                        "DELETE FROM memory_entries WHERE scope = ?", (scope.value,))
                    cleared_count = cursor.rowcount
                    self.sqlite_conn.commit()
                
                self.logger.info(f"Cleared {cleared_count} entries from scope {scope.value}")
                
            except Exception as e:
                self.logger.error(f"Failed to clear scope {scope.value}: {str(e)}")
        
        return cleared_count
    
    def cleanup_expired(self) -> int:
        """Clean up expired entries"""
        cleaned_count = 0
        now = datetime.now()
        
        with self._lock:
            try:
                if self.config.backend == StorageBackend.MEMORY:
                    expired_keys = [
                        key for key, entry in self._memory_store.items()
                        if entry.expires_at and now > entry.expires_at
                    ]
                    for key in expired_keys:
                        del self._memory_store[key]
                    cleaned_count = len(expired_keys)
                
                elif self.config.backend == StorageBackend.SQLITE:
                    cursor = self.sqlite_conn.execute(
                        "DELETE FROM memory_entries WHERE expires_at < ?", (now,))
                    cleaned_count = cursor.rowcount
                    self.sqlite_conn.commit()
                
                if cleaned_count > 0:
                    self.logger.info(f"Cleaned up {cleaned_count} expired entries")
                
            except Exception as e:
                self.logger.error(f"Cleanup failed: {str(e)}")
        
        return cleaned_count
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        stats = {
            'backend': self.config.backend.value,
            'total_entries': 0,
            'by_scope': {},
            'memory_usage': 0,
            'expired_entries': 0
        }
        
        try:
            if self.config.backend == StorageBackend.MEMORY:
                stats['total_entries'] = len(self._memory_store)
                now = datetime.now()
                
                for entry in self._memory_store.values():
                    scope = entry.scope.value
                    stats['by_scope'][scope] = stats['by_scope'].get(scope, 0) + 1
                    
                    if entry.expires_at and now > entry.expires_at:
                        stats['expired_entries'] += 1
                
                # Estimate memory usage
                import sys
                stats['memory_usage'] = sum(
                    sys.getsizeof(entry.value) for entry in self._memory_store.values()
                )
            
            elif self.config.backend == StorageBackend.SQLITE:
                cursor = self.sqlite_conn.execute("SELECT COUNT(*) FROM memory_entries")
                stats['total_entries'] = cursor.fetchone()[0]
                
                cursor = self.sqlite_conn.execute(
                    "SELECT scope, COUNT(*) FROM memory_entries GROUP BY scope"
                )
                stats['by_scope'] = dict(cursor.fetchall())
        
        except Exception as e:
            self.logger.error(f"Failed to get memory stats: {str(e)}")
            stats['error'] = str(e)
        
        return stats
    
    def create_context(self, context_id: str, parent_context: Optional[str] = None) -> 'MemoryContext':
        """Create a memory context"""
        return MemoryContext(self, context_id, parent_context)
    
    # Backend-specific implementations
    def _store_sqlite(self, entry: MemoryEntry):
        """Store entry in SQLite"""
        serialized_value = pickle.dumps(entry.value) if self.config.compression else json.dumps(entry.value, default=str).encode()
        metadata_json = json.dumps(entry.metadata) if entry.metadata else None
        
        self.sqlite_conn.execute('''
            INSERT OR REPLACE INTO memory_entries 
            (key, value, scope, created_at, updated_at, expires_at, metadata, access_count, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.key, serialized_value, entry.scope.value, entry.created_at, 
            entry.updated_at, entry.expires_at, metadata_json, 
            entry.access_count, entry.last_accessed
        ))
        self.sqlite_conn.commit()
    
    def _retrieve_sqlite(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve entry from SQLite"""
        cursor = self.sqlite_conn.execute(
            "SELECT * FROM memory_entries WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        _, value_data, scope, created_at, updated_at, expires_at, metadata_json, access_count, last_accessed = row
        
        # Deserialize value
        if self.config.compression:
            value = pickle.loads(value_data)
        else:
            value = json.loads(value_data.decode())
        
        # Parse metadata
        metadata = json.loads(metadata_json) if metadata_json else {}
        
        return MemoryEntry(
            key=key,
            value=value,
            scope=ContextScope(scope),
            created_at=datetime.fromisoformat(created_at),
            updated_at=datetime.fromisoformat(updated_at),
            expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
            metadata=metadata,
            access_count=access_count,
            last_accessed=datetime.fromisoformat(last_accessed) if last_accessed else None
        )
    
    def _store_redis(self, entry: MemoryEntry):
        """Store entry in Redis"""
        key = f"agentium:memory:{entry.key}"
        
        entry_data = asdict(entry)
        entry_data['scope'] = entry.scope.value
        entry_data['created_at'] = entry.created_at.isoformat()
        entry_data['updated_at'] = entry.updated_at.isoformat()
        
        if entry.expires_at:
            entry_data['expires_at'] = entry.expires_at.isoformat()
            ttl = int((entry.expires_at - datetime.now()).total_seconds())
        else:
            ttl = None
        
        if entry.last_accessed:
            entry_data['last_accessed'] = entry.last_accessed.isoformat()
        
        serialized_data = json.dumps(entry_data, default=str)
        
        if ttl:
            self.redis_client.setex(key, ttl, serialized_data)
        else:
            self.redis_client.set(key, serialized_data)
    
    def _retrieve_redis(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve entry from Redis"""
        redis_key = f"agentium:memory:{key}"
        data = self.redis_client.get(redis_key)
        
        if not data:
            return None
        
        entry_data = json.loads(data)
        
        return MemoryEntry(
            key=key,
            value=entry_data['value'],
            scope=ContextScope(entry_data['scope']),
            created_at=datetime.fromisoformat(entry_data['created_at']),
            updated_at=datetime.fromisoformat(entry_data['updated_at']),
            expires_at=datetime.fromisoformat(entry_data['expires_at']) if entry_data.get('expires_at') else None,
            metadata=entry_data.get('metadata', {}),
            access_count=entry_data.get('access_count', 0),
            last_accessed=datetime.fromisoformat(entry_data['last_accessed']) if entry_data.get('last_accessed') else None
        )
    
    def _store_file(self, entry: MemoryEntry):
        """Store entry in file"""
        filename = f"{self._hash_key(entry.key)}.pkl"
        file_path = self.file_backend_dir / filename
        
        with open(file_path, 'wb') as f:
            pickle.dump(entry, f)
    
    def _retrieve_file(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve entry from file"""
        filename = f"{self._hash_key(key)}.pkl"
        file_path = self.file_backend_dir / filename
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load file entry {key}: {str(e)}")
            return None
    
    def _hash_key(self, key: str) -> str:
        """Hash key for filename"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def _update_access_stats(self, key: str, entry: MemoryEntry):
        """Update access statistics in storage"""
        # Implementation depends on backend
        pass


class MemoryContext:
    """Context-aware memory interface"""
    
    def __init__(self, memory_helper: MemoryHelper, context_id: str, parent_context: Optional[str] = None):
        self.memory_helper = memory_helper
        self.context_id = context_id
        self.parent_context = parent_context
        self.logger = LoggerUtils.get_logger(__name__)
    
    def store(self, key: str, value: Any, ttl: Optional[int] = None, metadata: Optional[Dict] = None) -> bool:
        """Store value in context"""
        context_key = f"{self.context_id}:{key}"
        return self.memory_helper.store(context_key, value, ContextScope.SESSION, ttl, metadata)
    
    def retrieve(self, key: str, default: Any = None) -> Any:
        """Retrieve value from context with inheritance"""
        context_key = f"{self.context_id}:{key}"
        sentinel = object()  # Create a sentinel object to detect if key exists
        value = self.memory_helper.retrieve(context_key, sentinel)
        
        # If not found in current context, check parent context
        if value is sentinel and self.parent_context:
            parent_key = f"{self.parent_context}:{key}"
            value = self.memory_helper.retrieve(parent_key, default)
        elif value is sentinel:
            value = default
        
        return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Alias for retrieve method"""
        return self.retrieve(key, default)
    
    def delete(self, key: str) -> bool:
        """Delete value from context"""
        context_key = f"{self.context_id}:{key}"
        return self.memory_helper.delete(context_key)
    
    def clear(self) -> int:
        """Clear all values in context"""
        keys = self.memory_helper.search(f"{self.context_id}:")
        cleared_count = 0
        
        for key in keys:
            if self.memory_helper.delete(key):
                cleared_count += 1
        
        return cleared_count
    
    def list_keys(self) -> List[str]:
        """List keys in context"""
        context_keys = self.memory_helper.search(f"{self.context_id}:")
        return [key.replace(f"{self.context_id}:", "") for key in context_keys]