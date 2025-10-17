#!/usr/bin/env python
"""
PyInstaller 打包腳本

使用方法:
    python build.py

輸出位置:
    - Windows: dist/ModelArkVideoGenerator.exe
    - macOS: dist/ModelArkVideoGenerator.app
    - Linux: dist/ModelArkVideoGenerator
"""

import PyInstaller.__main__
import sys
import os
import platform


def build():
    """執行打包"""

    print("\n" + "=" * 60)
    print("🚀 開始打包 ModelArk Video Generator")
    print("=" * 60 + "\n")

    # 基本配置
    args = [
        'main.py',
        '--name=ModelArkVideoGenerator',
        '--onefile',  # 單一執行檔
        '--clean',    # 清理舊檔案
        '--noconfirm',  # 不詢問覆蓋
    ]

    # 添加數據文件（Windows 使用 ; 分隔符，其他平台使用 :）
    separator = ';' if sys.platform == 'win32' else ':'
    args.extend([
        f'--add-data=templates{separator}templates',
        f'--add-data=static{separator}static',
        f'--add-data=config.txt.example{separator}.',
        f'--add-data=README_DIST.md{separator}.',
    ])

    # 隱藏導入（避免 PyInstaller 遺漏）
    hidden_imports = [
        'app',
        'app.api_client',
        'app.models',
        'app.routes',
        'app.task_manager',
        'app.utils',
        'byteplussdkarkruntime',
        'byteplussdkarkruntime.resources',
        'sqlalchemy.sql.default_comparator',
        'sqlalchemy.ext.declarative',
        'werkzeug.security',
        'flask',
        'flask.json',
        'requests',
        'cryptography',
        'cryptography.fernet',
        'apscheduler.schedulers.background',
        'apscheduler.triggers.interval',
        'apscheduler.executors.pool',
        'apscheduler.jobstores.memory',
        'threading',
        'webbrowser',
    ]

    for imp in hidden_imports:
        args.append(f'--hidden-import={imp}')

    # 排除不需要的模組（減小體積）
    exclude_modules = [
        'matplotlib',
        'pandas',
        'numpy',
        'PIL',
        'tkinter',
        'test',
        'unittest',
    ]

    for mod in exclude_modules:
        args.append(f'--exclude-module={mod}')

    # 平台特定配置
    if sys.platform == 'darwin':  # macOS
        print("📦 打包平台: macOS")
        args.extend([
            '--windowed',  # GUI 模式（不顯示終端）
            # '--icon=static/assets/icon.icns',  # 需要先創建圖標文件
        ])
    elif sys.platform == 'win32':  # Windows
        print("📦 打包平台: Windows")
        args.extend([
            '--windowed',  # GUI 模式（不顯示 cmd）
            # '--icon=static/assets/icon.ico',  # 需要先創建圖標文件
        ])
    elif sys.platform.startswith('linux'):  # Linux
        print("📦 打包平台: Linux")
        # Linux 不使用 --windowed，保持終端輸出

    # 執行打包
    print("\n正在打包，請稍候...\n")

    try:
        PyInstaller.__main__.run(args)

        print("\n" + "=" * 60)
        print("✅ 打包完成！")
        print("=" * 60)

        # 輸出結果位置
        dist_dir = os.path.join(os.getcwd(), 'dist')
        if sys.platform == 'win32':
            exe_path = os.path.join(dist_dir, 'ModelArkVideoGenerator.exe')
        elif sys.platform == 'darwin':
            exe_path = os.path.join(dist_dir, 'ModelArkVideoGenerator.app')
        else:
            exe_path = os.path.join(dist_dir, 'ModelArkVideoGenerator')

        print(f"\n📦 執行檔位置:")
        print(f"   {exe_path}")

        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path if not exe_path.endswith('.app') else exe_path.replace('.app', '')) / (1024 * 1024)
            print(f"\n📏 檔案大小: {size_mb:.1f} MB")

        print("\n💡 使用提示:")
        print("   1. 在執行檔所在目錄創建 config.txt 文件")
        print("      - 第一行：BytePlus API Key")
        print("      - 第二行：視頻生成端點 ID（ep-xxxxx）")
        print("   2. 雙擊執行檔即可運行")
        print("   3. 應用會自動在瀏覽器打開 http://127.0.0.1:5001")
        print("   4. 詳細說明請查看 README_DIST.md")
        print("\n📦 建議打包內容:")
        print("   - ModelArkVideoGenerator.exe")
        print("   - config.txt.example")
        print("   - README_DIST.md")
        print("\n" + "=" * 60 + "\n")

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ 打包失敗！")
        print("=" * 60)
        print(f"\n錯誤信息: {str(e)}\n")
        sys.exit(1)


def check_dependencies():
    """檢查打包依賴"""
    print("🔍 檢查打包環境...\n")

    # 檢查 PyInstaller
    try:
        import PyInstaller
        print(f"✓ PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("❌ 未安裝 PyInstaller")
        print("   請運行: pip install pyinstaller")
        return False

    # 檢查其他依賴
    required_packages = [
        'flask',
        'requests',
        'sqlalchemy',
        'apscheduler',
        'cryptography',
        'byteplussdkarkruntime'
    ]

    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"❌ 未安裝 {package}")
            return False

    print("\n✅ 所有依賴已就緒\n")
    return True


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("ModelArk Video Generator - 打包工具")
    print("=" * 60 + "\n")

    # 檢查依賴
    if not check_dependencies():
        print("\n請先安裝所有依賴: pip install -r requirements.txt\n")
        sys.exit(1)

    # 執行打包
    build()
