const { createApp } = Vue;

createApp({
    data() {
        return {
            tasks: [],
            newTask: {
                prompt: '',
                ratio: '16:9',
                duration: 5,
                resolution: '720p',
                seed: null,
                camera_fixed: false
            },
            showSettings: false,
            apiKey: '',
            apiKeyConfigured: false,
            previewTaskId: null,
            polling: null,
            isCreating: false
        }
    },
    mounted() {
        this.checkSettings();
        this.loadTasks();
        // 每 5 秒輪詢更新任務狀態
        this.polling = setInterval(() => {
            this.loadTasks();
        }, 5000);
    },
    beforeUnmount() {
        if (this.polling) {
            clearInterval(this.polling);
        }
    },
    methods: {
        async loadTasks() {
            try {
                const response = await axios.get('/api/tasks');
                this.tasks = response.data.tasks || [];
            } catch (error) {
                console.error('載入任務失敗:', error);
                this.showError('載入任務失敗: ' + (error.response?.data?.error || error.message));
            }
        },

        buildParameterString() {
            // Build parameter string according to BytePlus API format
            const params = [];

            // --rt (ratio)
            if (this.newTask.ratio) {
                params.push(`--rt ${this.newTask.ratio}`);
            }

            // --dur (duration in seconds)
            if (this.newTask.duration) {
                params.push(`--dur ${this.newTask.duration}`);
            }

            // --fps (always 24 for BytePlus)
            params.push('--fps 24');

            // --rs (resolution)
            if (this.newTask.resolution) {
                params.push(`--rs ${this.newTask.resolution}`);
            }

            // --seed (optional)
            if (this.newTask.seed !== null && this.newTask.seed !== '') {
                params.push(`--seed ${this.newTask.seed}`);
            }

            // --cf (camera fixed)
            params.push(`--cf ${this.newTask.camera_fixed ? 'true' : 'false'}`);

            return params.join(' ');
        },

        async createTask() {
            if (!this.newTask.prompt.trim()) {
                this.showError('請輸入提示詞');
                return;
            }

            if (!this.apiKeyConfigured) {
                this.showError('請先配置 API Key');
                this.showSettings = true;
                return;
            }

            this.isCreating = true;

            try {
                // Build parameter string and append to prompt
                const paramString = this.buildParameterString();
                const fullPrompt = `${this.newTask.prompt.trim()} ${paramString}`;

                // Send only the prompt (with parameters embedded)
                const response = await axios.post('/api/tasks', {
                    prompt: fullPrompt
                });

                // 清空表單
                this.newTask.prompt = '';
                this.newTask.ratio = '16:9';
                this.newTask.duration = 5;
                this.newTask.resolution = '720p';
                this.newTask.seed = null;
                this.newTask.camera_fixed = false;

                // 立即刷新任務列表
                await this.loadTasks();

                this.showSuccess('任務創建成功！');
            } catch (error) {
                console.error('創建任務失敗:', error);
                this.showError('創建失敗: ' + (error.response?.data?.error || error.message));
            } finally {
                this.isCreating = false;
            }
        },

        async deleteTask(taskId) {
            if (!confirm('確定要刪除此任務嗎？')) {
                return;
            }

            try {
                await axios.delete(`/api/tasks/${taskId}`);
                await this.loadTasks();
                this.showSuccess('任務已刪除');
            } catch (error) {
                console.error('刪除任務失敗:', error);
                this.showError('刪除失敗: ' + (error.response?.data?.error || error.message));
            }
        },

        previewVideo(taskId) {
            this.previewTaskId = taskId;
        },

        async checkSettings() {
            try {
                const response = await axios.get('/api/settings');
                this.apiKeyConfigured = response.data.api_key_configured || false;

                if (!this.apiKeyConfigured) {
                    // 如果沒有配置 API Key，自動顯示設置面板
                    setTimeout(() => {
                        this.showSettings = true;
                    }, 1000);
                }
            } catch (error) {
                console.error('檢查設置失敗:', error);
            }
        },

        async saveSettings() {
            if (!this.apiKey.trim()) {
                this.showError('請輸入 API Key');
                return;
            }

            try {
                await axios.post('/api/settings', { api_key: this.apiKey });
                this.showSettings = false;
                this.apiKey = '';
                this.apiKeyConfigured = true;

                // 提示用戶可能需要重啟
                if (confirm('設置已保存！為了使更改生效，建議重啟應用程式。\n\n是否要重新載入頁面？')) {
                    window.location.reload();
                } else {
                    this.showSuccess('設置已保存');
                }
            } catch (error) {
                console.error('保存設置失敗:', error);
                this.showError('保存失敗: ' + (error.response?.data?.error || error.message));
            }
        },

        async refreshTasks() {
            await this.loadTasks();
            this.showSuccess('已刷新');
        },

        getStatusColor(status) {
            const colors = {
                'pending': 'bg-yellow-500',
                'processing': 'bg-blue-500',
                'completed': 'bg-green-500',
                'failed': 'bg-red-500',
                'cancelled': 'bg-gray-500'
            };
            return colors[status] || 'bg-gray-500';
        },

        getStatusBadge(status) {
            const badges = {
                'pending': 'bg-yellow-100 text-yellow-800',
                'processing': 'bg-blue-100 text-blue-800',
                'completed': 'bg-green-100 text-green-800',
                'failed': 'bg-red-100 text-red-800',
                'cancelled': 'bg-gray-100 text-gray-800'
            };
            return badges[status] || 'bg-gray-100 text-gray-800';
        },

        getStatusText(status) {
            const texts = {
                'pending': '⏳ 等待中',
                'processing': '🔄 生成中',
                'completed': '✅ 已完成',
                'failed': '❌ 失敗',
                'cancelled': '🚫 已取消'
            };
            return texts[status] || status;
        },

        formatDate(dateString) {
            if (!dateString) return 'N/A';
            try {
                const date = new Date(dateString);
                return date.toLocaleString('zh-TW', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } catch (e) {
                return dateString;
            }
        },

        showSuccess(message) {
            // 簡單的成功提示
            const toast = document.createElement('div');
            toast.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
            toast.textContent = '✓ ' + message;
            document.body.appendChild(toast);
            setTimeout(() => {
                toast.remove();
            }, 3000);
        },

        showError(message) {
            // 簡單的錯誤提示
            const toast = document.createElement('div');
            toast.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
            toast.textContent = '✗ ' + message;
            document.body.appendChild(toast);
            setTimeout(() => {
                toast.remove();
            }, 5000);
        }
    }
}).mount('#app');
