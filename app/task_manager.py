"""
後台任務管理器
功能：
- 定時輪詢任務狀態
- 自動更新數據庫
- 完成時自動下載視頻
"""

from apscheduler.schedulers.background import BackgroundScheduler
from app.api_client import BytePlusAPIClient
from app.models import Task
from datetime import datetime
import logging
import threading


class TaskManager:
    """後台任務管理器"""

    def __init__(self, api_client: BytePlusAPIClient, db_session, update_interval: int = 10):
        """
        初始化任務管理器

        Args:
            api_client: BytePlus API 客戶端
            db_session: SQLAlchemy session
            update_interval: 更新間隔（秒），默認 10 秒
        """
        self.api_client = api_client
        self.db_session = db_session
        self.update_interval = update_interval
        self.scheduler = BackgroundScheduler()

        # 添加定時任務
        self.scheduler.add_job(
            self.update_tasks,
            'interval',
            seconds=update_interval,
            id='update_tasks',
            max_instances=1  # 避免任務重疊執行
        )

        logging.info(f"任務管理器已初始化，更新間隔: {update_interval} 秒")

    def start(self):
        """啟動任務管理器"""
        if not self.scheduler.running:
            self.scheduler.start()
            logging.info("任務管理器已啟動")
        else:
            logging.warning("任務管理器已經在運行中")

    def stop(self):
        """停止任務管理器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logging.info("任務管理器已停止")
        else:
            logging.warning("任務管理器未運行")

    def pause(self):
        """暫停任務管理器（不查詢任務）"""
        if self.scheduler.running:
            self.scheduler.pause()
            logging.info("任務管理器已暫停（無待處理任務）")

    def resume(self):
        """恢復任務管理器"""
        if self.scheduler.running and self.scheduler.state == 2:  # STATE_PAUSED = 2
            self.scheduler.resume()
            logging.info("任務管理器已恢復運行")
        elif not self.scheduler.running:
            self.start()
            logging.info("任務管理器已重新啟動")

    def update_tasks(self):
        """更新所有進行中的任務"""
        try:
            # 查詢所有進行中的任務
            pending_tasks = self.db_session.query(Task).filter(
                Task.status.in_(['pending', 'processing'])
            ).all()

            if not pending_tasks:
                logging.info("沒有待處理任務，暫停 TaskManager")
                self.pause()
                return

            logging.info(f"開始更新 {len(pending_tasks)} 個任務")

            # 收集需要下載視頻的任務（只需要 task_id 和 video_url）
            tasks_to_download = []

            for task in pending_tasks:
                try:
                    video_url = self._update_single_task(task)
                    if video_url:
                        tasks_to_download.append((task.task_id, video_url))
                except Exception as e:
                    logging.error(f"更新任務 {task.task_id} 時出錯: {str(e)}")
                    # 繼續處理其他任務

            # 提交所有狀態更改（此時完成的任務已經變為 completed，下次輪詢不會再查到）
            self.db_session.commit()
            logging.info("任務更新完成")

            # 在新線程中異步下載視頻，完全不阻塞輪詢
            for task_id, video_url in tasks_to_download:
                thread = threading.Thread(
                    target=self._download_video_for_task,
                    args=(task_id, video_url),
                    daemon=True
                )
                thread.start()
                logging.info(f"已啟動後台線程下載視頻: {task_id}")

        except Exception as e:
            logging.error(f"更新任務時出錯: {str(e)}")
            self.db_session.rollback()

    def _update_single_task(self, task: Task):
        """
        更新單個任務

        Args:
            task: 任務對象

        Returns:
            str: 如果任務完成且有視頻 URL，返回視頻 URL；否則返回 None
        """
        # 查詢最新狀態
        result = self.api_client.get_task(task.task_id)

        if result.get('code') == 0:
            data = result.get('data', {})

            # 更新狀態
            old_status = task.status
            task.status = data.get('status', task.status)
            task.progress = data.get('progress', task.progress)
            task.updated_at = datetime.utcnow()

            # 記錄狀態變化
            if old_status != task.status:
                logging.info(f"任務 {task.task_id} 狀態變化: {old_status} -> {task.status}")

            # 如果任務完成，保存視頻 URL 並返回（稍後下載）
            if task.status == 'completed' and data.get('video_url'):
                task.video_url = data.get('video_url')
                task.thumbnail_url = data.get('thumbnail_url')
                task.completed_at = datetime.utcnow()
                logging.info(f"任務 {task.task_id} 已完成，待下載視頻")
                return task.video_url

            # 如果任務失敗，記錄錯誤
            elif task.status == 'failed':
                task.error_message = data.get('error_message', '任務處理失敗')
                logging.error(f"任務 {task.task_id} 失敗: {task.error_message}")

        else:
            # API 調用失敗
            error_msg = result.get('message', '未知錯誤')
            logging.error(f"查詢任務 {task.task_id} 失敗: {error_msg}")

            # 如果是任務不存在的錯誤，標記為失敗
            if result.get('code') == 40004:
                task.status = 'failed'
                task.error_message = '任務不存在'

        return None

    def _download_video_for_task(self, task_id: str, video_url: str):
        """
        為已完成的任務下載視頻（在後台線程中執行）

        Args:
            task_id: 任務 ID
            video_url: 視頻 URL
        """
        try:
            local_path = f"static/videos/{task_id}.mp4"

            logging.info(f"開始下載視頻: {task_id}")
            downloaded_path = self.api_client.download_video(
                video_url,
                local_path
            )

            if downloaded_path:
                # 下載成功後更新數據庫（在新線程中需要查詢任務）
                task = self.db_session.query(Task).filter_by(task_id=task_id).first()
                if task:
                    task.local_video_path = downloaded_path
                    self.db_session.commit()
                    logging.info(f"視頻下載成功: {task_id} -> {downloaded_path}")
            else:
                logging.error(f"視頻下載失敗: {task_id}")
                # 不標記為失敗，因為視頻 URL 仍然可用

        except Exception as e:
            logging.error(f"下載視頻時發生錯誤 {task_id}: {str(e)}")

    def force_update_task(self, task_id: str):
        """
        強制更新指定任務

        Args:
            task_id: 任務 ID

        Returns:
            bool: 是否成功更新
        """
        try:
            task = self.db_session.query(Task).filter_by(task_id=task_id).first()
            if not task:
                logging.warning(f"任務不存在: {task_id}")
                return False

            self._update_single_task(task)
            self.db_session.commit()
            logging.info(f"強制更新任務成功: {task_id}")
            return True

        except Exception as e:
            logging.error(f"強制更新任務失敗: {str(e)}")
            self.db_session.rollback()
            return False

    def get_status(self):
        """
        獲取任務管理器狀態

        Returns:
            dict: 狀態信息
        """
        pending_count = self.db_session.query(Task).filter(
            Task.status.in_(['pending', 'processing'])
        ).count()

        return {
            'running': self.scheduler.running,
            'update_interval': self.update_interval,
            'pending_tasks': pending_count,
            'next_run': str(self.scheduler.get_job('update_tasks').next_run_time) if self.scheduler.running else None
        }
