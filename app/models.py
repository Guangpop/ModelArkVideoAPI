"""
SQLite 數據庫模型
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class Task(Base):
    """視頻生成任務模型"""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    task_id = Column(String(100), unique=True, nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    model = Column(String(100), nullable=True)
    status = Column(String(20), default='pending', index=True)  # pending, processing, completed, failed, cancelled
    progress = Column(Float, default=0.0)
    video_url = Column(String(500), nullable=True)
    local_video_path = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    duration = Column(Integer, default=5)
    aspect_ratio = Column(String(10), default='16:9')
    fps = Column(Integer, default=24)
    quality = Column(String(20), default='high')
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def to_dict(self):
        """轉換為字典格式"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'prompt': self.prompt,
            'model': self.model,
            'status': self.status,
            'progress': self.progress,
            'video_url': self.video_url,
            'local_video_path': self.local_video_path,
            'thumbnail_url': self.thumbnail_url,
            'duration': self.duration,
            'aspect_ratio': self.aspect_ratio,
            'fps': self.fps,
            'quality': self.quality,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self):
        return f"<Task {self.task_id} - {self.status}>"


class Settings(Base):
    """應用設置模型"""
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Setting {self.key}>"


def init_db(db_path='data/tasks.db'):
    """
    初始化數據庫

    Args:
        db_path: 數據庫文件路徑

    Returns:
        Session: SQLAlchemy Session 類
    """
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session


def get_or_create_session(db_path='data/tasks.db'):
    """
    獲取或創建數據庫 session

    Args:
        db_path: 數據庫文件路徑

    Returns:
        session: SQLAlchemy session 實例
    """
    Session = init_db(db_path)
    return Session()
