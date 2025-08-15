# easy_dataset_cli/prompts.py
"""LLMプロンプト定義とマークダウンファイル読み込み"""

from pathlib import Path


def load_prompt_template(template_name: str) -> str:
    """プロンプトテンプレートをマークダウンファイルから読み込む"""
    prompt_dir = Path(__file__).parent / "prompts"
    template_path = prompt_dir / f"{template_name}.md"
    
    if not template_path.exists():
        raise FileNotFoundError(f"プロンプトテンプレートが見つかりません: {template_path}")
    
    return template_path.read_text(encoding="utf-8")


def get_qa_generation_prompt() -> str:
    """Q&A生成プロンプトを取得"""
    return load_prompt_template("qa_generation")


def get_qa_generation_with_fulltext_prompt() -> str:
    """全文+チャンク対応Q&A生成プロンプトを取得"""
    return load_prompt_template("qa_generation_with_fulltext")


def get_ga_definition_generation_prompt() -> str:
    """GA定義生成プロンプトを取得"""
    return load_prompt_template("ga_definition_generation")


def get_qa_generation_with_thinking_prompt() -> str:
    """思考フロー対応Q&A生成プロンプトを取得"""
    return load_prompt_template("qa_generation_with_thinking")
