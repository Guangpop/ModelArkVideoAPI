"""
工具函數（加密、日誌、API Key 管理等）
"""

import logging
import os
import sys
import uuid
from pathlib import Path
from cryptography.fernet import Fernet
from app.models import Settings


def get_key_file_path():
    """
    獲取加密密鑰文件路徑

    Returns:
        Path: 加密密鑰文件路徑
    """
    if getattr(sys, 'frozen', False):
        # 打包後的 exe：放在 exe 同目錄
        return Path(sys.executable).parent / '.encryption_key'
    else:
        # 開發環境：放在 config 目錄
        return Path('config/.key')


def get_encryption_key():
    """
    獲取或生成加密密鑰

    如果無法寫入文件，使用基於機器 UUID 的固定密鑰

    Returns:
        bytes: 加密密鑰
    """
    key_file = get_key_file_path()

    # 嘗試從文件讀取
    try:
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
    except Exception as e:
        logging.warning(f"讀取密鑰文件失敗: {str(e)}")

    # 嘗試創建新密鑰並保存
    try:
        key = Fernet.generate_key()
        key_file.parent.mkdir(parents=True, exist_ok=True)
        with open(key_file, 'wb') as f:
            f.write(key)
        logging.info(f"已生成新的加密密鑰: {key_file}")
        return key
    except Exception as e:
        # 無法寫入文件，使用基於機器 UUID 的固定密鑰
        logging.warning(f"無法寫入密鑰文件: {str(e)}")
        logging.warning("使用基於機器的固定密鑰")

        # 使用機器 UUID 生成固定密鑰
        try:
            machine_id = str(uuid.getnode()).encode()
        except:
            machine_id = b'default-machine-id'

        # 生成32字節的密鑰並轉為 base64（Fernet 要求）
        import base64
        import hashlib
        key_bytes = hashlib.sha256(machine_id).digest()
        return base64.urlsafe_b64encode(key_bytes)


# 初始化 Fernet 加密器
_cipher = Fernet(get_encryption_key())


def encrypt(text):
    """
    加密文本

    Args:
        text: 要加密的文本

    Returns:
        str: 加密後的文本（base64 編碼）
    """
    if not text:
        return None
    return _cipher.encrypt(text.encode()).decode()


def decrypt(encrypted_text):
    """
    解密文本

    Args:
        encrypted_text: 加密的文本

    Returns:
        str: 解密後的文本
    """
    if not encrypted_text:
        return None
    try:
        return _cipher.decrypt(encrypted_text.encode()).decode()
    except Exception as e:
        logging.error(f"解密失敗: {str(e)}")
        return None


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


def get_api_key(db_session):
    """
    獲取 API Key

    從執行檔同目錄的 config.txt 文件讀取
    格式：第一行為 API Key

    Args:
        db_session: SQLAlchemy session（保留參數以兼容現有代碼）

    Returns:
        str: API Key，如果不存在則返回 None
    """
    # 從 config.txt 文件讀取
    try:
        config_file = get_config_file_path()

        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) >= 1:
                    api_key = lines[0].strip()
                    if api_key:
                        logging.info("✓ 從 config.txt 文件讀取 API Key")
                        return api_key
    except Exception as e:
        logging.warning(f"讀取 config.txt 失敗: {str(e)}")

    # 沒有找到配置文件或 API Key 為空
    logging.warning("⚠ 未找到 config.txt 或 API Key 未設置")
    return None


def save_api_key(db_session, api_key):
    """
    加密並保存 API Key 到數據庫

    Args:
        db_session: SQLAlchemy session
        api_key: 要保存的 API Key

    Returns:
        bool: 是否成功保存
    """
    try:
        encrypted_key = encrypt(api_key)
        setting = db_session.query(Settings).filter_by(key='api_key').first()

        if setting:
            setting.value = encrypted_key
        else:
            setting = Settings(key='api_key', value=encrypted_key)
            db_session.add(setting)

        db_session.commit()
        logging.info("API Key 已成功保存")
        return True
    except Exception as e:
        logging.error(f"保存 API Key 失敗: {str(e)}")
        db_session.rollback()
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
