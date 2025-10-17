"""
工具函數（日誌、API Key 管理等）
"""

import logging
import os
import sys
from pathlib import Path


def get_config_file_path():
    """
    獲取配置文件路徑

    Returns:
        Path: config.txt 文件路徑
    """
    # 獲取執行檔所在目錄（支持打包後的執行檔）
    if getattr(sys, 'frozen', False):
        # 打包後的執行檔
        app_dir = Path(sys.executable).parent
    else:
        # 開發環境
        app_dir = Path.cwd()

    return app_dir / 'config.txt'


def get_api_key(db_session=None):
    """
    獲取 API Key

    直接從執行檔同目錄的 config.txt 文件讀取
    格式：第一行為 API Key

    Args:
        db_session: 保留參數以兼容現有代碼（不再使用）

    Returns:
        str: API Key，如果不存在則返回 None
    """
    try:
        config_file = get_config_file_path()

        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) >= 1:
                    api_key = lines[0].strip()
                    if api_key and api_key != 'your-api-key-here':
                        logging.info("✓ 從 config.txt 讀取 API Key")
                        return api_key
    except Exception as e:
        logging.warning(f"讀取 config.txt 失敗: {str(e)}")

    logging.warning("⚠ 未找到 config.txt 或 API Key 未設置")
    return None


def save_api_key(db_session, api_key):
    """
    保存 API Key（已廢棄，僅保留以兼容現有代碼）

    API Key 現在直接從 config.txt 讀取，不再存儲到數據庫

    Args:
        db_session: SQLAlchemy session（不再使用）
        api_key: API Key（不再使用）

    Returns:
        bool: 總是返回 False
    """
    logging.warning("save_api_key() 已廢棄，請直接編輯 config.txt 文件")
    return False


def get_model_id():
    """
    獲取 Model/Endpoint ID

    從執行檔同目錄的 config.txt 文件讀取
    格式：第二行為 Model/Endpoint ID

    Returns:
        str: Model/Endpoint ID，如果不存在則返回 None
    """
    # 從 config.txt 文件讀取
    try:
        config_file = get_config_file_path()

        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    model_id = lines[1].strip()
                    if model_id:
                        logging.info(f"✓ 從 config.txt 文件讀取 Model ID: {model_id}")
                        return model_id
    except Exception as e:
        logging.warning(f"讀取 config.txt 失敗: {str(e)}")

    # 沒有找到配置文件或 Model ID 為空
    logging.warning("⚠ 未找到 config.txt 或 Model ID 未設置")
    return None


def setup_logging(log_file='logs/app.log', log_level='INFO'):
    """
    配置日誌系統

    Args:
        log_file: 日誌文件路徑（相對於工作目錄）
        log_level: 日誌級別
    """
    # 獲取正確的工作目錄
    if getattr(sys, 'frozen', False):
        # 打包後：exe 同目錄
        work_dir = Path(sys.executable).parent
    else:
        # 開發環境：當前目錄
        work_dir = Path.cwd()

    # 配置日誌格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # 設置日誌處理器
    handlers = [logging.StreamHandler()]

    # 嘗試添加文件處理器
    try:
        log_path = work_dir / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path, encoding='utf-8'))
    except Exception as e:
        # 無法創建日誌文件，只輸出到控制台
        print(f"Warning: Cannot create log file: {e}")

    # 配置 logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )

    # 抑制一些第三方庫的日誌
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    logging.info("日誌系統已初始化")


def ensure_directories():
    """確保所有必要的目錄都存在"""
    # 獲取正確的工作目錄
    if getattr(sys, 'frozen', False):
        # 打包後：exe 同目錄
        work_dir = Path(sys.executable).parent
    else:
        # 開發環境：當前目錄
        work_dir = Path.cwd()

    # 打包後只需要創建數據和日誌目錄（static/templates 已打包在 exe 中）
    if getattr(sys, 'frozen', False):
        directories = [
            'data',
            'logs',
        ]
    else:
        directories = [
            'data',
            'static/videos',
            'static/css',
            'static/js',
            'static/assets',
            'logs',
            'config',
            'templates'
        ]

    for directory in directories:
        try:
            (work_dir / directory).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logging.warning(f"無法創建目錄 {directory}: {str(e)}")

    logging.info("目錄結構已確保完整")
