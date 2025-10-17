"""
應用配置管理
"""

import os
from pathlib import Path

# 基礎路徑
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
STATIC_DIR = BASE_DIR / 'static'
VIDEO_DIR = STATIC_DIR / 'videos'
LOG_DIR = BASE_DIR / 'logs'
CONFIG_DIR = BASE_DIR / 'config'

# 確保目錄存在
for directory in [DATA_DIR, VIDEO_DIR, LOG_DIR, CONFIG_DIR]:
    directory.mkdir(exist_ok=True)

# 數據庫配置
DATABASE_URL = f'sqlite:///{DATA_DIR / "tasks.db"}'

# BytePlus API 配置
BYTEPLUS_BASE_URL = os.getenv(
    'BYTEPLUS_BASE_URL',
    'https://ark.ap-southeast.bytepluses.com/api/v3'
)

# Flask 配置
FLASK_CONFIG = {
    'HOST': '127.0.0.1',
    'PORT': 5001,  # 改為 5001，避免與 macOS AirPlay Receiver 衝突
    'DEBUG': False
}

# 任務管理器配置
TASK_UPDATE_INTERVAL = 10  # 秒
MAX_CONCURRENT_DOWNLOADS = 3

# 日誌配置
LOG_FILE = LOG_DIR / 'app.log'
LOG_LEVEL = 'INFO'

# 安全配置
SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32).hex())
