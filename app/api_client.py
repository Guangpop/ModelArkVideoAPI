"""
BytePlus ModelArk API 客戶端
使用官方 SDK: byteplussdkarkruntime
"""

import logging
from typing import Optional, Dict, Any
from byteplussdkarkruntime import Ark
from app.utils import get_model_id


def map_api_status_to_db(api_status: str) -> str:
    """
    將 BytePlus API 狀態映射到數據庫狀態

    API 狀態: pending, running, succeeded, failed
    數據庫狀態: pending, processing, completed, failed, cancelled

    Args:
        api_status: BytePlus API 返回的狀態

    Returns:
        str: 數據庫狀態
    """
    status_mapping = {
        'pending': 'pending',
        'running': 'processing',
        'succeeded': 'completed',
        'failed': 'failed'
    }
    return status_mapping.get(api_status, api_status)


class BytePlusAPIClient:
    """BytePlus ModelArk API 客戶端（使用官方 SDK）"""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """
        初始化 API 客戶端

        Args:
            api_key: BytePlus API Key
            base_url: API 基礎 URL，默認使用亞太地區端點
        """
        self.api_key = api_key
        self.base_url = base_url or "https://ark.ap-southeast.bytepluses.com/api/v3"

        # 使用官方 SDK 初始化客戶端
        self.client = Ark(
            api_key=self.api_key,
            base_url=self.base_url
        )

        logging.info(f"BytePlus API 客戶端已初始化（使用官方 SDK），Base URL: {self.base_url}")

    def create_task(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        創建視頻生成任務

        Args:
            prompt: 視頻生成提示詞（純文本）
            **kwargs: 其他參數
                - model: 端點 ID，從 config.txt 讀取（格式如 'ep-xxxxx'）
                  在 BytePlus ModelArk 控制台創建的 Online Inference 端點
                - image_url: 圖片 URL（可選，用於 image-to-video）

        注意：
            - duration、aspect_ratio、fps、quality 等參數需要在創建端點時配置
            - 本方法使用官方 SDK 的標準調用格式

        Returns:
            dict: 統一的響應格式
        """
        try:
            # 構建 content 數組（按照官方 API 格式）
            content = []

            # 添加文本提示（text-to-video 或 image-to-video 的描述）
            content.append({
                "type": "text",
                "text": prompt
            })

            # 如果提供了圖片數組，添加圖片內容（image-to-video）
            # images: [{"url": "...", "role": "first_frame"/"last_frame"/"reference_image"}]
            images = kwargs.get('images')
            if images and isinstance(images, list):
                for img in images:
                    url = img.get('url')
                    role = img.get('role')

                    if not url:
                        continue

                    image_obj = {
                        "type": "image_url",
                        "image_url": {
                            "url": url
                        }
                    }

                    # Add role if specified (required for first_last_frame and reference modes)
                    if role:
                        image_obj["role"] = role

                    content.append(image_obj)

            # 獲取模型/端點 ID（從配置文件讀取）
            model = kwargs.get("model") or get_model_id()

            if not model:
                logging.error("未配置 Model ID，請在 config.txt 中設置")
                return {
                    "code": -1,
                    "message": "未配置 Model ID，請在 config.txt 文件第二行設置端點 ID",
                    "data": None
                }

            logging.info(f"創建視頻生成任務，提示詞: {prompt[:50]}...")
            logging.debug(f"使用模型: {model}")
            logging.debug(f"完整 content: {content}")

            # 使用 SDK 創建任務（按照官方示例格式）
            result = self.client.content_generation.tasks.create(
                model=model,
                content=content
            )

            logging.info(f"任務創建成功: {result.id}")

            # 獲取 API 狀態並映射到數據庫狀態
            api_status = getattr(result, 'status', 'pending')
            db_status = map_api_status_to_db(api_status)

            # 轉換為統一格式
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "task_id": result.id,
                    "model": model,  # 使用傳入的 model 參數
                    "status": db_status,  # 使用映射後的數據庫狀態
                    "created_at": getattr(result, 'created_at', None)
                }
            }

        except Exception as e:
            logging.error(f"創建任務失敗: {str(e)}")
            return {
                "code": -1,
                "message": f"請求失敗: {str(e)}",
                "data": None
            }

    def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        查詢任務詳情

        Args:
            task_id: 任務 ID

        Returns:
            dict: 統一的響應格式
        """
        try:
            result = self.client.content_generation.tasks.get(task_id=task_id)

            logging.debug(f"查詢任務 {task_id}: {getattr(result, 'status', 'unknown')}")

            # 獲取 API 狀態並映射到數據庫狀態
            api_status = getattr(result, 'status', 'unknown')
            db_status = map_api_status_to_db(api_status)

            # 轉換為統一格式
            response = {
                "code": 0,
                "message": "success",
                "data": {
                    "task_id": result.id,
                    "model": getattr(result, 'model', None),
                    "status": db_status,  # 使用映射後的數據庫狀態
                    "created_at": getattr(result, 'created_at', None),
                    "updated_at": getattr(result, 'updated_at', None)
                }
            }

            # 如果任務完成，添加視頻 URL
            if api_status == "succeeded" and hasattr(result, 'content'):
                if hasattr(result.content, 'video_url'):
                    response["data"]["video_url"] = result.content.video_url
                if hasattr(result.content, 'last_frame_url'):
                    response["data"]["last_frame_url"] = result.content.last_frame_url

            # 如果任務失敗，添加錯誤信息
            if getattr(result, 'status', None) == "failed" and hasattr(result, 'error') and result.error:
                response["data"]["error"] = {
                    "code": result.error.code if hasattr(result.error, 'code') else "unknown",
                    "message": result.error.message if hasattr(result.error, 'message') else str(result.error)
                }

            # 添加使用信息
            if hasattr(result, 'usage') and result.usage:
                response["data"]["usage"] = {
                    "completion_tokens": result.usage.completion_tokens if hasattr(result.usage, 'completion_tokens') else 0
                }

            return response

        except Exception as e:
            logging.error(f"查詢任務失敗: {str(e)}")
            return {
                "code": -1,
                "message": f"請求失敗: {str(e)}",
                "data": None
            }

    def list_tasks(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        獲取任務列表

        Args:
            page: 頁碼
            page_size: 每頁數量

        Returns:
            dict: 統一的響應格式
        """
        try:
            result = self.client.content_generation.tasks.list(
                page_num=page,
                page_size=page_size
            )

            logging.debug(f"查詢任務列表，頁碼: {page}")

            # 轉換為統一格式
            tasks = []
            if hasattr(result, 'data') and result.data:
                for task in result.data:
                    api_status = getattr(task, 'status', 'unknown')
                    db_status = map_api_status_to_db(api_status)
                    tasks.append({
                        "task_id": task.id,
                        "model": getattr(task, 'model', None),
                        "status": db_status,  # 使用映射後的數據庫狀態
                        "created_at": getattr(task, 'created_at', None),
                        "updated_at": getattr(task, 'updated_at', None)
                    })

            return {
                "code": 0,
                "message": "success",
                "data": {
                    "tasks": tasks,
                    "total": result.total if hasattr(result, 'total') else len(tasks),
                    "page": page,
                    "page_size": page_size
                }
            }

        except Exception as e:
            logging.error(f"查詢任務列表失敗: {str(e)}")
            return {
                "code": -1,
                "message": f"請求失敗: {str(e)}",
                "data": None
            }

    def delete_task(self, task_id: str) -> Dict[str, Any]:
        """
        刪除任務

        Args:
            task_id: 任務 ID

        Returns:
            dict: 統一的響應格式
        """
        try:
            logging.info(f"刪除任務: {task_id}")

            self.client.content_generation.tasks.delete(task_id=task_id)

            logging.info(f"任務 {task_id} 已刪除")

            return {
                "code": 0,
                "message": "success",
                "data": {"task_id": task_id}
            }

        except Exception as e:
            logging.error(f"刪除任務失敗: {str(e)}")
            return {
                "code": -1,
                "message": f"請求失敗: {str(e)}",
                "data": None
            }

    def download_video(self, video_url: str, save_path: str) -> Optional[str]:
        """
        下載視頻文件

        Args:
            video_url: 視頻 URL
            save_path: 保存路徑

        Returns:
            str: 保存路徑，失敗返回 None
        """
        try:
            import requests
            from pathlib import Path

            logging.info(f"開始下載視頻: {video_url}")
            response = requests.get(video_url, stream=True, timeout=300)
            response.raise_for_status()

            # 確保目錄存在
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)

            # 下載視頻
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logging.info(f"視頻下載完成: {save_path}")
            return save_path

        except Exception as e:
            logging.error(f"下載視頻失敗: {str(e)}")
            return None

    def test_connection(self) -> bool:
        """
        測試 API 連接

        Returns:
            bool: 連接是否成功
        """
        try:
            # 嘗試查詢任務列表來測試連接
            result = self.list_tasks(page=1, page_size=1)
            if result.get('code') == 0:
                logging.info("API 連接測試成功")
                return True
            else:
                logging.warning(f"API 連接測試失敗: {result.get('message')}")
                return False
        except Exception as e:
            logging.error(f"API 連接測試異常: {str(e)}")
            return False
