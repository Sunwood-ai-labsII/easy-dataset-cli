# easy_dataset_cli/file_utils.py
"""ファイル操作関連のユーティリティ"""

from pathlib import Path
from typing import Dict, List
from collections import defaultdict
from rich.console import Console

console = Console()


def create_output_directories(base_dir: Path) -> Dict[str, Path]:
    """出力用のディレクトリ構造を作成する"""
    directories = {
        "base": base_dir,
        "ga": base_dir / "ga",
        "logs": base_dir / "logs",
        "qa": base_dir / "qa"
    }

    for dir_path in directories.values():
        dir_path.mkdir(parents=True, exist_ok=True)

    return directories


def save_ga_definitions_by_genre(ga_pairs: List[Dict[str, Dict[str, str]]], ga_dir: Path) -> None:
    """GAペアをGenreごとにマークダウンファイルに保存する"""
    genre_groups = defaultdict(list)

    # Genreごとにグループ化
    for pair in ga_pairs:
        genre_title = pair['genre']['title']
        genre_groups[genre_title].append(pair)

    # 各Genreごとにファイルを作成
    for genre_title, pairs in genre_groups.items():
        # ファイル名に使用できない文字を置換
        safe_filename = "".join(c for c in genre_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_filename = safe_filename.replace(' ', '_').lower()

        file_path = ga_dir / f"ga_definitions_{safe_filename}.md"

        content = f"# {genre_title}\n\n"

        for pair in pairs:
            content += f"## Genre: {pair['genre']['title']}\n"
            content += f"{pair['genre']['description']}\n\n"
            content += f"## Audience: {pair['audience']['title']}\n"
            content += f"{pair['audience']['description']}\n\n"
            content += "---\n\n"

        file_path.write_text(content, encoding="utf-8")
        console.print(f"[green]GA定義を保存しました:[/green] {file_path}")


def sanitize_filename(name: str) -> str:
    """ファイル名として安全な文字列に変換する"""
    return "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).rstrip()


def find_text_files(directory: Path) -> List[Path]:
    """指定されたディレクトリ内のテキストファイルを再帰的に検索する"""
    text_extensions = {'.txt', '.md', '.rst', '.org', '.tex', '.text'}
    text_files = []
    
    for file_path in directory.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in text_extensions:
            text_files.append(file_path)
    
    return sorted(text_files)


# バッチ処理ユーティリティは削除してシンプル化
