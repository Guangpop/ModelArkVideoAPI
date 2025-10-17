"""
Flask REST API 路由
"""

from flask import Blueprint, request, jsonify, send_file
from app.models import Task, Settings
from app.utils import save_api_key, get_api_key
from datetime import datetime
import logging
import os


def create_api_blueprint(app_context):
    """
    創建 API Blueprint

    Args:
        app_context: 應用上下文，包含 db_session、api_client、task_manager

    Returns:
        Blueprint: Flask Blueprint
    """
    api_bp = Blueprint('api', __name__, url_prefix='/api')

    # 從上下文中獲取對象的輔助函數
    def get_db_session():
        return app_context.db_session

    def get_api_client():
        return app_context.api_client

    def get_task_manager():
        return app_context.task_manager

    @api_bp.route('/tasks', methods=['GET'])
    def get_tasks():
        """獲取任務列表"""
        try:
            db_session = get_db_session()
            page = request.args.get('page', 1, type=int)
            page_size = request.args.get('page_size', 20, type=int)

            # 查詢任務（按創建時間倒序）
            tasks = db_session.query(Task).order_by(
                Task.created_at.desc()
            ).limit(page_size).offset((page - 1) * page_size).all()

            total = db_session.query(Task).count()

            return jsonify({
                'tasks': [task.to_dict() for task in tasks],
                'total': total,
                'page': page,
                'page_size': page_size
            })

        except Exception as e:
            logging.error(f"獲取任務列表失敗: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @api_bp.route('/tasks', methods=['POST'])
    def create_task():
        """創建新任務"""
        try:
            db_session = get_db_session()
            api_client = get_api_client()

            if not api_client:
                return jsonify({'error': '請先配置 API Key'}), 400

            data = request.json

            if not data or 'prompt' not in data:
                return jsonify({'error': '缺少必要參數: prompt'}), 400

            # 調用 BytePlus API 創建任務
            result = api_client.create_task(
                prompt=data['prompt'],
                model=data.get('model'),
                duration=data.get('duration'),
                aspect_ratio=data.get('aspect_ratio'),
                fps=data.get('fps'),
                quality=data.get('quality')
            )

            if result.get('code') == 0:
                # 儲存到數據庫
                task = Task(
                    task_id=result['data']['task_id'],
                    prompt=data['prompt'],
                    model=result['data'].get('model', 'unknown'),
                    duration=data.get('duration', 5),
                    aspect_ratio=data.get('aspect_ratio', '16:9'),
                    fps=data.get('fps', 24),
                    quality=data.get('quality', 'high')
                )
                db_session.add(task)
                db_session.commit()

                # 創建任務後，啟動 TaskManager（如果已暫停）
                task_manager = get_task_manager()
                if task_manager:
                    task_manager.resume()

                logging.info(f"任務創建成功: {task.task_id}")
                return jsonify(task.to_dict()), 201

            else:
                error_msg = result.get('message', '未知錯誤')
                logging.error(f"創建任務失敗: {error_msg}")
                return jsonify({'error': error_msg}), 400

        except Exception as e:
            logging.error(f"創建任務異常: {str(e)}")
            db_session.rollback()
            return jsonify({'error': str(e)}), 500

    @api_bp.route('/tasks/<task_id>', methods=['GET'])
    def get_task(task_id):
        """獲取任務詳情"""
        try:
            db_session = get_db_session()
            task = db_session.query(Task).filter_by(task_id=task_id).first()

            if task:
                return jsonify(task.to_dict())
            else:
                return jsonify({'error': '任務不存在'}), 404

        except Exception as e:
            logging.error(f"獲取任務詳情失敗: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @api_bp.route('/tasks/<task_id>', methods=['DELETE'])
    def delete_task(task_id):
        """刪除任務"""
        try:
            db_session = get_db_session()
            api_client = get_api_client()
            task = db_session.query(Task).filter_by(task_id=task_id).first()

            if task:
                # 調用 API 取消任務（如果還在進行中）
                if api_client and task.status in ['pending', 'processing']:
                    api_client.delete_task(task_id)

                # 刪除本地視頻文件
                if task.local_video_path and os.path.exists(task.local_video_path):
                    try:
                        os.remove(task.local_video_path)
                        logging.info(f"已刪除視頻文件: {task.local_video_path}")
                    except Exception as e:
                        logging.warning(f"刪除視頻文件失敗: {str(e)}")

                # 從數據庫刪除
                db_session.delete(task)
                db_session.commit()

                logging.info(f"任務已刪除: {task_id}")
                return jsonify({'message': '任務已刪除'})
            else:
                return jsonify({'error': '任務不存在'}), 404

        except Exception as e:
            logging.error(f"刪除任務失敗: {str(e)}")
            db_session.rollback()
            return jsonify({'error': str(e)}), 500

    @api_bp.route('/video/<task_id>', methods=['GET'])
    def get_video(task_id):
        """獲取視頻文件"""
        try:
            db_session = get_db_session()
            task = db_session.query(Task).filter_by(task_id=task_id).first()

            if not task:
                return jsonify({'error': '任務不存在'}), 404

            if task.status != 'completed':
                return jsonify({'error': '視頻尚未生成完成'}), 400

            if task.local_video_path and os.path.exists(task.local_video_path):
                return send_file(task.local_video_path, mimetype='video/mp4')
            elif task.video_url:
                # 如果本地沒有，重定向到原始 URL
                from flask import redirect
                return redirect(task.video_url)
            else:
                return jsonify({'error': '視頻不可用'}), 404

        except Exception as e:
            logging.error(f"獲取視頻失敗: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @api_bp.route('/settings', methods=['GET'])
    def get_settings():
        """獲取設置"""
        try:
            db_session = get_db_session()
            api_key = get_api_key(db_session)

            return jsonify({
                'api_key_configured': bool(api_key)
            })

        except Exception as e:
            logging.error(f"獲取設置失敗: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @api_bp.route('/settings', methods=['POST'])
    def update_settings():
        """更新設置"""
        try:
            db_session = get_db_session()
            data = request.json

            if 'api_key' in data:
                success = save_api_key(db_session, data['api_key'])
                if success:
                    logging.info("API Key 已更新")
                    # 重新初始化 API 客戶端
                    if hasattr(app_context, 'init_api_client'):
                        init_success = app_context.init_api_client()
                        if init_success:
                            return jsonify({'message': 'API Key 已保存並生效'})
                        else:
                            return jsonify({'message': 'API Key 已保存，但初始化失敗，請檢查 API Key 是否有效'})
                    return jsonify({'message': 'API Key 已保存'})
                else:
                    return jsonify({'error': '保存 API Key 失敗'}), 500

            return jsonify({'error': '沒有要更新的設置'}), 400

        except Exception as e:
            logging.error(f"更新設置失敗: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @api_bp.route('/status', methods=['GET'])
    def get_status():
        """獲取系統狀態"""
        try:
            db_session = get_db_session()
            api_client = get_api_client()
            task_manager = get_task_manager()

            task_manager_status = task_manager.get_status() if task_manager else {'running': False}

            return jsonify({
                'api_connected': bool(api_client),
                'task_manager': task_manager_status,
                'total_tasks': db_session.query(Task).count(),
                'pending_tasks': db_session.query(Task).filter(
                    Task.status.in_(['pending', 'processing'])
                ).count(),
                'completed_tasks': db_session.query(Task).filter_by(status='completed').count()
            })

        except Exception as e:
            logging.error(f"獲取狀態失敗: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @api_bp.route('/tasks/<task_id>/refresh', methods=['POST'])
    def refresh_task(task_id):
        """強制刷新任務狀態"""
        try:
            db_session = get_db_session()
            task_manager = get_task_manager()

            if task_manager:
                success = task_manager.force_update_task(task_id)
                if success:
                    task = db_session.query(Task).filter_by(task_id=task_id).first()
                    return jsonify(task.to_dict() if task else {})
                else:
                    return jsonify({'error': '刷新失敗'}), 500
            else:
                return jsonify({'error': '任務管理器未啟動'}), 503

        except Exception as e:
            logging.error(f"刷新任務失敗: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return api_bp
