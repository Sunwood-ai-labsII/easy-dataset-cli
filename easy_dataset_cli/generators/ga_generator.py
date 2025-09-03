#!/usr/bin/env python3
"""
GA定義生成機能
"""

import os
from pathlib import Path
from openai import OpenAI
from rich.console import Console
from dotenv import load_dotenv
import traceback
import json

# .envファイルを読み込む
load_dotenv()

console = Console()


def generate_ga_definitions(text_content: str, model: str, num_ga_pairs: int = None, max_context_length: int = 8000) -> str:
    """OpenAIクライアントを使い、元の文章からGAペア定義のXMLを生成する"""
    # LLMに渡すテキストは長すぎるとコストや性能に影響するため、先頭部分に限定する
    context = text_content[:max_context_length]
    console.print(f"[dim]コンテキスト長: {len(context)} 文字 (上限: {max_context_length})[/dim]")

    from ..prompts import get_ga_definition_generation_prompt
    prompt_template = get_ga_definition_generation_prompt()
    prompt = prompt_template.format(
        context=context,
        num_ga_pairs=num_ga_pairs if num_ga_pairs is not None else "3-5個の"
    )

    messages = [
        {"role": "system", "content": "あなたは、XML形式で厳密に出力する優秀なアシスタントです。"},
        {"role": "user", "content": prompt}
    ]

    # APIキーの確認
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        console.print("[bold red]OPENAI_API_KEYが設定されていません！[/bold red]")
        raise ValueError("OPENAI_API_KEYが必要です")

    # OpenAIクライアントの初期化
    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=api_key,
    )

    # リトライ+タイムアウト付きリクエスト
    import time
    import random
    max_retries = 3
    timeout_sec = int(os.getenv("EASY_DATASET_TIMEOUT", "120"))
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                timeout=timeout_sec
            )
            xml_content = response.choices[0].message.content
            console.print(f"[dim]LLMレスポンス長: {len(xml_content)} 文字[/dim]")
            return xml_content
        except Exception as error:
            last_err = error
            wait_s = min(2 ** attempt + random.random(), 10)
            console.print(f"[yellow]GA生成リトライ {attempt}/{max_retries} 失敗: {error}[/yellow]")
            if attempt < max_retries:
                console.print(f"[dim]{wait_s:.1f}s 待機後に再試行[/dim]")
                time.sleep(wait_s)
    console.print(f"[bold red]GA定義の生成に失敗:[/bold red] {last_err}")
    raise last_err
