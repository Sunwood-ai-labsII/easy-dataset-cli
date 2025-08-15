# easy_dataset_cli/qa_generator.py
"""Q&A生成関連機能"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict
from litellm import completion
from rich.console import Console
from dotenv import load_dotenv

from .prompts import (
    get_qa_generation_prompt,
    get_qa_generation_with_fulltext_prompt,
    get_ga_definition_generation_prompt
)
from .xml_utils import parse_qa_from_text_fallback

# .envファイルを読み込む
load_dotenv()

console = Console()


def generate_qa_for_chunk_with_ga_and_fulltext(
    chunk: str,
    full_text: str,
    model: str,
    ga_pair: Dict[str, Dict[str, str]],
    logs_dir: Path = None,
    num_qa_pairs: int = None
) -> List[Dict[str, str]]:
    """litellmを使い、1つのチャンクと全文、1つのGAペアからQ&Aペアのリストを生成する"""
    prompt_template = get_qa_generation_with_fulltext_prompt()
    prompt = prompt_template.format(
        chunk=chunk,
        full_text=full_text,
        genre_title=ga_pair['genre']['title'],
        genre_description=ga_pair['genre']['description'],
        audience_title=ga_pair['audience']['title'],
        audience_description=ga_pair['audience']['description'],
        num_qa_pairs=num_qa_pairs if num_qa_pairs is not None else "複数の"
    )

    messages = [
        {"role": "system", "content": "あなたは、XML形式で厳密に出力する優秀なアシスタントです。XMLの特殊文字（&, <, >, \", '）は適切にエスケープし、改行は含めずに出力してください。"},
        {"role": "user", "content": prompt}
    ]

    # OpenRouter用の環境変数設定
    os.environ["OPENROUTER_API_KEY"] = os.getenv("OPENROUTER_API_KEY", "")

    try:
        response = completion(model=model, messages=messages)
        xml_content = response.choices[0].message.content

        # rawレスポンスを保存（オプション）
        if logs_dir:
            genre_safe = "".join(c for c in ga_pair['genre']['title'] if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
            audience_safe = "".join(c for c in ga_pair['audience']['title'] if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
            raw_filename = f"qa_fulltext_raw_{genre_safe}_{audience_safe}.md"
            raw_file_path = logs_dir / raw_filename
            raw_file_path.write_text(xml_content, encoding="utf-8")

        return _parse_qa_response(xml_content)

    except Exception as general_error:
        console.print(
            f"[bold red]チャンクとGAペアからのQ&A生成中にエラーが発生しました:[/bold red] "
            f"{general_error}"
        )
        console.print(
            f"[dim]Genre: {ga_pair['genre']['title']}, "
            f"Audience: {ga_pair['audience']['title']}[/dim]"
        )
        return []


def generate_qa_for_chunk_with_ga(
    chunk: str,
    model: str,
    ga_pair: Dict[str, Dict[str, str]],
    logs_dir: Path = None,
    num_qa_pairs: int = None
) -> List[Dict[str, str]]:
    """litellmを使い、1つのチャンクと1つのGAペアからQ&Aペアのリストを生成する"""
    prompt_template = get_qa_generation_prompt()
    prompt = prompt_template.format(
        context=chunk,
        genre_title=ga_pair['genre']['title'],
        genre_description=ga_pair['genre']['description'],
        audience_title=ga_pair['audience']['title'],
        audience_description=ga_pair['audience']['description'],
        num_qa_pairs=num_qa_pairs if num_qa_pairs is not None else "複数の"
    )

    messages = [
        {"role": "system", "content": "あなたは、XML形式で厳密に出力する優秀なアシスタントです。XMLの特殊文字（&, <, >, \", '）は適切にエスケープし、改行は含めずに出力してください。"},
        {"role": "user", "content": prompt}
    ]

    # OpenRouter用の環境変数設定
    os.environ["OPENROUTER_API_KEY"] = os.getenv("OPENROUTER_API_KEY", "")

    try:
        response = completion(model=model, messages=messages)
        xml_content = response.choices[0].message.content

        # rawレスポンスを保存（オプション）
        if logs_dir:
            genre_safe = "".join(c for c in ga_pair['genre']['title'] if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
            audience_safe = "".join(c for c in ga_pair['audience']['title'] if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
            raw_filename = f"qa_raw_{genre_safe}_{audience_safe}.md"
            raw_file_path = logs_dir / raw_filename
            raw_file_path.write_text(xml_content, encoding="utf-8")

        return _parse_qa_response(xml_content)

    except Exception as general_error:
        console.print(
            f"[bold red]チャンクとGAペアからのQ&A生成中にエラーが発生しました:[/bold red] "
            f"{general_error}"
        )
        console.print(
            f"[dim]Genre: {ga_pair['genre']['title']}, "
            f"Audience: {ga_pair['audience']['title']}[/dim]"
        )
        return []


def generate_ga_definitions(text_content: str, model: str, num_ga_pairs: int = None) -> str:
    """litellmを使い、元の文章からGAペア定義のXMLを生成する"""
    # LLMに渡すテキストは長すぎるとコストや性能に影響するため、先頭部分に限定する
    context = text_content[:8000]
    console.print(f"[dim]コンテキスト長: {len(context)} 文字[/dim]")

    prompt_template = get_ga_definition_generation_prompt()
    prompt = prompt_template.format(
        context=context,
        num_ga_pairs=num_ga_pairs if num_ga_pairs is not None else "3-5個の"
    )

    messages = [
        {"role": "system", "content": "あなたは、XML形式で厳密に出力する優秀なアシスタントです。"},
        {"role": "user", "content": prompt}
    ]

    # OpenRouter用の環境変数設定
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        console.print("[bold red]OPENROUTER_API_KEYが設定されていません！[/bold red]")
        raise ValueError("OPENROUTER_API_KEYが必要です")

    os.environ["OPENROUTER_API_KEY"] = api_key

    # OpenRouterのモデル名に変換（必要に応じて）
    if "openrouter" not in model and not model.startswith("openrouter/"):
        if model.startswith("gpt-"):
            model = f"openrouter/openai/{model}"
        elif model.startswith("claude-"):
            model = f"openrouter/anthropic/{model}"
        else:
            # デフォルトでopenrouterプレフィックスを追加
            model = f"openrouter/{model}"

    try:
        response = completion(model=model, messages=messages)
        xml_content = response.choices[0].message.content
        console.print(f"[dim]LLMレスポンス長: {len(xml_content)} 文字[/dim]")
        return xml_content
    except Exception as error:
        console.print(f"[bold red]GA定義の生成中にエラーが発生しました:[/bold red] {error}")
        raise


def _parse_qa_response(xml_content: str) -> List[Dict[str, str]]:
    """Q&A生成レスポンスのXMLを解析する（共通処理）"""
    qa_pairs = []

    # LLMからの出力には余分なテキストが含まれることがあるため、XML部分のみを抽出
    xml_start = xml_content.find("<QAPairs>")
    xml_end = xml_content.rfind("</QAPairs>")

    if xml_start != -1 and xml_end != -1:
        clean_xml = xml_content[xml_start: xml_end + len("</QAPairs>")]

        try:
            root = ET.fromstring(clean_xml)

            for pair_node in root.findall('Pair'):
                question_node = pair_node.find('Question')
                answer_node = pair_node.find('Answer')

                if question_node is not None and answer_node is not None:
                    qa_pairs.append({
                        "question": question_node.text or "",
                        "answer": answer_node.text or ""
                    })

        except ET.ParseError:
            # XMLパースに失敗した場合、手動でテキスト解析
            console.print("[yellow]XMLパースエラー、手動解析を試行中...[/yellow]")
            qa_pairs = parse_qa_from_text_fallback(clean_xml)

    if not qa_pairs:
        console.print(f"[bold red]LLMが生成したXMLの解析に失敗しました[/bold red]")
        console.print(f"[dim]受信したテキスト: {xml_content[:200]}...[/dim]")

    return qa_pairs
