# GitHub Actions 自動打包說明

本項目使用 GitHub Actions 自動構建 Windows 可執行文件。

## 觸發方式

### 1. 手動觸發（推薦）
在 GitHub 網頁上：
1. 進入 **Actions** 頁面
2. 選擇 **Build Windows Executable** workflow
3. 點擊 **Run workflow** 按鈕
4. 選擇分支後點擊 **Run workflow**

### 2. 推送 Tag 觸發（自動發布）
```bash
# 創建並推送 tag
git tag v1.0.0
git push origin v1.0.0
```

這會自動：
- 構建 Windows exe
- 創建 GitHub Release
- 上傳發行版壓縮包

## 構建產物

構建完成後，可以在以下位置找到文件：

### Artifacts（保留 90 天）
在 Actions 運行頁面下載：
- `ModelArkVideoGenerator-{version}-win64/` - 解壓後的文件夾
- `ModelArkVideoGenerator-{version}-win64-zip` - 壓縮包

### Releases（永久保存）
如果是通過 tag 觸發，會自動創建 Release：
- 訪問 **Releases** 頁面
- 下載 `ModelArkVideoGenerator-{version}-win64.zip`

## 構建內容

壓縮包包含：
- `ModelArkVideoGenerator.exe` - 主程序
- `config.txt.example` - 配置文件範例
- `README.md` - 使用說明

## 本地測試

在推送前可以本地測試 workflow：
```bash
# 安裝 act (GitHub Actions 本地運行工具)
# macOS:
brew install act

# Windows:
choco install act-cli

# 運行 workflow
act workflow_dispatch
```

## 注意事項

1. **構建時間**：首次構建約需 5-10 分鐘
2. **配額**：GitHub Actions 免費帳號有使用限制（公開倉庫無限制）
3. **敏感信息**：確保 `config.txt` 在 `.gitignore` 中，不會被上傳
