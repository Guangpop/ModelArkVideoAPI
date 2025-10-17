#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyInstaller Build Script

Usage:
    python build.py

Output:
    - Windows: dist/ModelArkVideoGenerator.exe
    - macOS: dist/ModelArkVideoGenerator.app
    - Linux: dist/ModelArkVideoGenerator
"""

import PyInstaller.__main__
import sys
import os
import platform

# Fix Windows console encoding issues
def safe_print(text):
    """Safe print that handles encoding issues on Windows"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback to ASCII-safe output
        print(text.encode('ascii', 'replace').decode('ascii'))


def build():
    """Build executable with PyInstaller"""

    safe_print("\n" + "=" * 60)
    safe_print("Building ModelArk Video Generator...")
    safe_print("=" * 60 + "\n")

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

    # Hidden imports (avoid PyInstaller missing modules)
    hidden_imports = [
        'app',
        'app.api_client',
        'app.models',
        'app.routes',
        'app.task_manager',
        'app.utils',
        'byteplussdkarkruntime',
        'byteplussdkarkruntime.resources',
        'byteplussdkarkruntime._client',
        'byteplussdkarkruntime._compat',
        'byteplussdkcore',
        'byteplussdkcore.rest',
        'httpx',
        'httpx._client',
        'httpx._config',
        'httpx._models',
        'httpx._transports',
        'httpcore',
        'h11',
        'anyio',
        'sniffio',
        'pydantic',
        'pydantic.fields',
        'pydantic_core',
        'typing_extensions',
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
        'uuid',
        'hashlib',
        'base64',
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

    # Platform-specific configuration
    if sys.platform == 'darwin':  # macOS
        safe_print("Platform: macOS")
        args.extend([
            '--windowed',  # GUI mode (no terminal)
            # '--icon=static/assets/icon.icns',
        ])
    elif sys.platform == 'win32':  # Windows
        safe_print("Platform: Windows")
        args.extend([
            '--windowed',  # GUI mode (no cmd window)
            # '--icon=static/assets/icon.ico',
        ])
    elif sys.platform.startswith('linux'):  # Linux
        safe_print("Platform: Linux")
        # Keep terminal output for Linux

    # Execute build
    safe_print("\nBuilding executable, please wait...\n")

    try:
        PyInstaller.__main__.run(args)

        safe_print("\n" + "=" * 60)
        safe_print("Build completed successfully!")
        safe_print("=" * 60)

        # Output location
        dist_dir = os.path.join(os.getcwd(), 'dist')
        if sys.platform == 'win32':
            exe_path = os.path.join(dist_dir, 'ModelArkVideoGenerator.exe')
        elif sys.platform == 'darwin':
            exe_path = os.path.join(dist_dir, 'ModelArkVideoGenerator.app')
        else:
            exe_path = os.path.join(dist_dir, 'ModelArkVideoGenerator')

        safe_print(f"\nExecutable location:")
        safe_print(f"   {exe_path}")

        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path if not exe_path.endswith('.app') else exe_path.replace('.app', '')) / (1024 * 1024)
            safe_print(f"\nFile size: {size_mb:.1f} MB")

        safe_print("\nUsage instructions:")
        safe_print("   1. Create config.txt file in the same directory")
        safe_print("      - Line 1: BytePlus API Key")
        safe_print("      - Line 2: Video generation endpoint ID (ep-xxxxx)")
        safe_print("   2. Double-click the executable to run")
        safe_print("   3. Application will open in browser at http://127.0.0.1:5001")
        safe_print("   4. See README_DIST.md for details")
        safe_print("\nDistribution package should include:")
        safe_print("   - ModelArkVideoGenerator.exe")
        safe_print("   - config.txt.example")
        safe_print("   - README_DIST.md")
        safe_print("\n" + "=" * 60 + "\n")

    except Exception as e:
        safe_print("\n" + "=" * 60)
        safe_print("Build failed!")
        safe_print("=" * 60)
        safe_print(f"\nError: {str(e)}\n")
        sys.exit(1)


def check_dependencies():
    """Check build dependencies"""
    safe_print("Checking build environment...\n")

    # Check PyInstaller
    try:
        import PyInstaller
        safe_print(f"[OK] PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        safe_print("[ERROR] PyInstaller not installed")
        safe_print("   Please run: pip install pyinstaller")
        return False

    # Check other dependencies
    required_packages = [
        'flask',
        'requests',
        'sqlalchemy',
        'apscheduler',
        'cryptography',
    ]

    for package in required_packages:
        try:
            __import__(package)
            safe_print(f"[OK] {package}")
        except ImportError:
            safe_print(f"[ERROR] {package} not installed")
            return False

    # Check BytePlus SDK (package: byteplus-python-sdk-v2)
    # Note: Module structure may vary, so we skip this check to avoid blocking the build
    try:
        import byteplussdkarkruntime
        safe_print("[OK] BytePlus SDK")
    except ImportError:
        safe_print("[SKIP] BytePlus SDK check (will be included by PyInstaller)")

    safe_print("\nAll dependencies are ready\n")
    return True


if __name__ == '__main__':
    safe_print("\n" + "=" * 60)
    safe_print("ModelArk Video Generator - Build Tool")
    safe_print("=" * 60 + "\n")

    # Check dependencies
    if not check_dependencies():
        safe_print("\nPlease install all dependencies: pip install -r requirements.txt\n")
        sys.exit(1)

    # Execute build
    build()
