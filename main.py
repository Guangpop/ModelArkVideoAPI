"""
應用程式主入口
"""

from flask import Flask, render_template
from app.routes import create_api_blueprint
from app.models import init_db
from app.task_manager import TaskManager
from app.api_client import BytePlusAPIClient
from app.utils import get_api_key, setup_logging, ensure_directories
import config
import webbrowser
import threading
import logging
import sys
import atexit


class AppContext:
    """應用上下文，用於存儲可變的全局對象"""
    def __init__(self):
        self.api_client = None
        self.task_manager = None
        self.db_session = None

def create_app():
    """創建並配置 Flask 應用"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.SECRET_KEY

    # 設置日誌
    setup_logging(str(config.LOG_FILE), config.LOG_LEVEL)
    logging.info("=" * 50)
    logging.info("ModelArk Video Generator 啟動中...")
    logging.info("=" * 50)

    # 確保所有必要目錄存在
    ensure_directories()

    # 初始化數據庫
    logging.info("初始化數據庫...")
    Session = init_db(str(config.DATA_DIR / 'tasks.db'))
    db_session = Session()

    # 創建應用上下文
    app_context = AppContext()
    app_context.db_session = db_session

    # 初始化 API 客戶端和任務管理器
    def init_api_client():
        """初始化或重新初始化 API 客戶端和任務管理器"""
        # 先停止現有的任務管理器
        if app_context.task_manager:
            logging.info("停止現有任務管理器...")
            app_context.task_manager.stop()
            app_context.task_manager = None

        # 重置 API 客戶端
        app_context.api_client = None

        # 獲取 API Key
        api_key = get_api_key(db_session)

        if api_key:
            logging.info("API Key 已配置，初始化 API 客戶端...")
            try:
                api_client = BytePlusAPIClient(api_key, config.BYTEPLUS_BASE_URL)

                # 測試 API 連接
                if api_client.test_connection():
                    logging.info("✓ API 連接測試成功")
                    app_context.api_client = api_client

                    # 啟動任務管理器
                    logging.info("啟動任務管理器...")
                    task_manager = TaskManager(
                        api_client,
                        db_session,
                        config.TASK_UPDATE_INTERVAL
                    )
                    task_manager.start()
                    app_context.task_manager = task_manager
                    logging.info("✓ 任務管理器已啟動")
                    return True
                else:
                    logging.warning("⚠ API 連接測試失敗，請檢查 API Key 是否有效")
                    return False
            except Exception as e:
                logging.error(f"初始化 API 客戶端失敗: {str(e)}")
                return False
        else:
            logging.warning("⚠ 未配置 API Key，請在設置中配置")
            return False

    # 首次初始化
    init_api_client()

    # 將初始化函數附加到上下文
    app_context.init_api_client = init_api_client

    # 註冊關閉處理器
    def shutdown_task_manager():
        if app_context.task_manager:
            logging.info("關閉任務管理器...")
            app_context.task_manager.stop()

    atexit.register(shutdown_task_manager)

    # 註冊 API 路由
    api_bp = create_api_blueprint(app_context)
    app.register_blueprint(api_bp)

    @app.route('/')
    def index():
        """主頁"""
        return render_template('index.html')

    @app.errorhandler(404)
    def not_found(error):
        """404 錯誤處理"""
        return {'error': '資源不存在'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        """500 錯誤處理"""
        logging.error(f"內部錯誤: {str(error)}")
        return {'error': '內部伺服器錯誤'}, 500

    return app


def open_browser():
    """延遲後開啟瀏覽器"""
    import time
    time.sleep(1.5)  # 等待伺服器啟動
    url = f"http://{config.FLASK_CONFIG['HOST']}:{config.FLASK_CONFIG['PORT']}"
    logging.info(f"正在開啟瀏覽器: {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        logging.error(f"無法自動開啟瀏覽器: {str(e)}")
        logging.info(f"請手動訪問: {url}")


def main():
    """主函數"""
    try:
        # 創建應用
        app = create_app()

        # 在背景線程中開啟瀏覽器
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()

        # 啟動提示
        print("\n" + "=" * 60)
        print("🚀 ModelArk Video Generator 已啟動")
        print("=" * 60)
        print(f"📱 應用地址: http://{config.FLASK_CONFIG['HOST']}:{config.FLASK_CONFIG['PORT']}")
        print(f"📂 數據目錄: {config.DATA_DIR}")
        print(f"📹 視頻目錄: {config.VIDEO_DIR}")
        print(f"📋 日誌文件: {config.LOG_FILE}")
        print("=" * 60)
        print("按 Ctrl+C 停止應用")
        print("=" * 60 + "\n")

        # 啟動 Flask
        app.run(
            host=config.FLASK_CONFIG['HOST'],
            port=config.FLASK_CONFIG['PORT'],
            debug=config.FLASK_CONFIG['DEBUG'],
            use_reloader=False  # 禁用重載器，避免雙重啟動
        )

    except KeyboardInterrupt:
        print("\n\n👋 應用已停止")
        sys.exit(0)
    except Exception as e:
        logging.error(f"應用啟動失敗: {str(e)}", exc_info=True)
        print(f"\n❌ 錯誤: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
