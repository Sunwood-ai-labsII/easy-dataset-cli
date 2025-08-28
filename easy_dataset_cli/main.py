#!/usr/bin/env python3
"""
Easy Dataset CLI - メインエントリーポイント
"""

from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# commandsからアプリをインポート
from .commands import app, print_logo

def main():
    """メインエントリーポイント関数"""
    print_logo()
    app()

if __name__ == "__main__":
    main()
