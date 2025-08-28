#!/usr/bin/env python3
"""
全文対応Q&A生成機能
"""

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from typing import List, Dict
from openai import OpenAI
from rich.console import Console
from dotenv import load_dotenv
import traceback
import json
from datetime import datetime

from ..prompts import get_qa_generation_with_fulltext_prompt
from ..xml_utils import parse_qa_from_text_fallback

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
    """OpenAIクライアントを使い、1つのチャンクと全文、1つのGAペアからQ&Aペアのリストを生成する"""
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
        {"role": "system", "content": "あなたは、XML形式で厳密に出力する優秀なアシスタントです。通常のXMLの特殊文字（&, \", '）は適切にエスケープしてください。ただし、<Question>、<Answer>、<think>タグはそのまま使用してください。改行は含めずに出力してください。"},
        {"role": "user", "content": prompt}
    ]

    # OpenAIクライアントの初期化
    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    # タイムスタンプ付きログファイル名を生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    genre_safe = "".join(c for c in ga_pair['genre']['title'] if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
    audience_safe = "".join(c for c in ga_pair['audience']['title'] if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')

    try:
        # リクエストログを保存
        if logs_dir:
            request_log = {
                "timestamp": timestamp,
                "model": model,
                "genre": ga_pair['genre']['title'],
                "audience": ga_pair['audience']['title'],
                "prompt_length": len(prompt),
                "messages": messages
            }
            request_filename = f"request_{genre_safe}_{audience_safe}_{timestamp}.json"
            request_file_path = logs_dir / request_filename
            with open(request_file_path, 'w', encoding='utf-8') as f:
                json.dump(request_log, f, ensure_ascii=False, indent=2)
            console.print(f"[dim]リクエストログを保存: {request_filename}[/dim]")

        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        xml_content = response.choices[0].message.content

        # レスポンスログを保存
        if logs_dir:
            response_log = {
                "timestamp": timestamp,
                "model": model,
                "genre": ga_pair['genre']['title'],
                "audience": ga_pair['audience']['title'],
                "response_length": len(xml_content),
                "response_content": xml_content
            }
            response_filename = f"response_{genre_safe}_{audience_safe}_{timestamp}.json"
            response_file_path = logs_dir / response_filename
            with open(response_file_path, 'w', encoding='utf-8') as f:
                json.dump(response_log, f, ensure_ascii=False, indent=2)
            console.print(f"[dim]レスポンスログを保存: {response_filename}[/dim]")

        # rawレスポンスを保存（オプション）
        if logs_dir:
            raw_filename = f"qa_fulltext_raw_{genre_safe}_{audience_safe}_{timestamp}.md"
            raw_file_path = logs_dir / raw_filename
            raw_file_path.write_text(xml_content, encoding="utf-8")

        qa_pairs = _parse_qa_response(xml_content, logs_dir, genre_safe, audience_safe, timestamp)

        # 生成したQAを保存
        if qa_pairs and logs_dir:
            qa_filename = f"qa_pairs_{genre_safe}_{audience_safe}_{timestamp}.xml"
            qa_file_path = logs_dir / qa_filename

            _save_qa_pairs_to_xml(qa_pairs, logs_dir, qa_filename)

        return qa_pairs

    except Exception as general_error:
        # 詳細なエラー情報を表示
        console.print(f"[bold red]チャンクとGAペアからのQ&A生成中にエラーが発生しました:[/bold red]")
        console.print(f"[bold red]エラータイプ:[/bold red] {type(general_error).__name__}")
        console.print(f"[bold red]エラーメッセージ:[/bold red] {str(general_error)}")
        console.print(f"[bold red]トレースバック:[/bold red]")
        console.print(traceback.format_exc())
        console.print(f"[dim]Genre: {ga_pair['genre']['title']}, Audience: {ga_pair['audience']['title']}[/dim]")

        # エラーログを保存
        if logs_dir:
            error_log = {
                "timestamp": timestamp,
                "model": model,
                "genre": ga_pair['genre']['title'],
                "audience": ga_pair['audience']['title'],
                "error_type": type(general_error).__name__,
                "error_message": str(general_error),
                "traceback": traceback.format_exc()
            }
            error_filename = f"error_{genre_safe}_{audience_safe}_{timestamp}.json"
            error_file_path = logs_dir / error_filename
            with open(error_file_path, 'w', encoding='utf-8') as f:
                json.dump(error_log, f, ensure_ascii=False, indent=2)
            console.print(f"[dim]エラーログを保存: {error_filename}[/dim]")

        return []


def _parse_qa_response(xml_content: str, logs_dir: Path = None, genre_safe: str = None, audience_safe: str = None, timestamp: str = None) -> List[Dict[str, str]]:
    """Q&A生成レスポンスのXMLを解析する（共通処理）"""
    qa_pairs = []

    # LLMからの出力の前処理：不要なテキストを除去
    cleaned_content = _clean_llm_response(xml_content)

    # XML部分のみを抽出 - 優先的に<QAPairs>タグを探す
    xml_start = cleaned_content.find("<QAPairs>")
    xml_end = cleaned_content.rfind("</QAPairs>")

    # <QAPairs>タグが見つからない場合は<Pair>タグで抽出を試行
    if xml_start == -1 or xml_end == -1:
        console.print("[yellow]<QAPairs>タグが見つからないため、<Pair>タグで抽出を試行します...[/yellow]")
        xml_start = cleaned_content.find("<Pair>")
        xml_end = cleaned_content.rfind("</Pair>")

        # <Pair>タグで囲まれた部分を抽出
        if xml_start != -1 and xml_end != -1:
            # すべての<Pair>...</Pair>を抽出
            import re
            pair_pattern = r'<Pair>.*?</Pair>'
            pair_matches = re.findall(pair_pattern, cleaned_content, re.DOTALL)

            for pair_match in pair_matches:
                # 各PairからQuestionとAnswerを抽出
                question_match = re.search(r'<Question>(.*?)</Question>', pair_match, re.DOTALL)
                answer_match = re.search(r'<Answer>(.*?)</Answer>', pair_match, re.DOTALL)

                if question_match and answer_match:
                    qa_pairs.append({
                        "question": _decode_xml_entities(question_match.group(1).strip()),
                        "answer": _decode_xml_entities(answer_match.group(1).strip())
                    })

            if qa_pairs:
                console.print(f"[green]✓[/green] <Pair>タグから{len(qa_pairs)}件のQ&Aを抽出しました")
                return qa_pairs

    if xml_start != -1 and xml_end != -1:
        clean_xml = cleaned_content[xml_start: xml_end + len("</QAPairs>")]

        # XML解析用のログを保存
        if logs_dir and genre_safe and audience_safe and timestamp:
            xml_debug_log = {
                "timestamp": timestamp,
                "original_xml_content": xml_content[:500],
                "cleaned_xml_content": cleaned_content[:500],
                "final_xml_content": clean_xml,
                "xml_length": len(clean_xml)
            }
            xml_debug_filename = f"xml_debug_{genre_safe}_{audience_safe}_{timestamp}.json"
            xml_debug_file_path = logs_dir / xml_debug_filename
            with open(xml_debug_file_path, 'w', encoding='utf-8') as f:
                json.dump(xml_debug_log, f, ensure_ascii=False, indent=2)

        try:
            root = ET.fromstring(clean_xml)

            for pair_node in root.findall('Pair'):
                question_node = pair_node.find('Question')
                answer_node = pair_node.find('Answer')

                if question_node is not None and answer_node is not None:
                    question_text = question_node.text or ""

                    # <Answer>要素内の内容を適切に取得
                    if len(answer_node) > 0:
                        # サブエレメントがある場合（<think>タグなど）
                        answer_parts = []

                        # Answer要素の直接のテキスト（<think>より前）
                        if answer_node.text:
                            answer_parts.append(answer_node.text.strip())

                        # 各サブエレメントのtail（サブエレメントの後のテキスト）
                        for child in answer_node:
                            if child.tag == 'think':
                                # <think>タグの内容を取得
                                think_content = child.text or ""
                                answer_parts.append(f"<think>{think_content}</think>")

                            # サブエレメントの後のテキスト
                            if child.tail:
                                answer_parts.append(child.tail.strip())

                        answer_text = "".join(answer_parts)
                    else:
                        # サブエレメントがない場合は通常のテキスト
                        answer_text = answer_node.text or ""

                    # XMLエンティティデコード
                    question_text = _decode_xml_entities(question_text)
                    answer_text = _decode_xml_entities(answer_text)

                    qa_pairs.append({
                        "question": question_text,
                        "answer": answer_text
                    })

        except ET.ParseError as parse_error:
            # XMLパースに失敗した場合、手動でテキスト解析
            console.print("[yellow]XMLパースエラー、自動解析を試行中...[/yellow]")
            console.print(f"[dim]パースエラー詳細: {str(parse_error)}[/dim]")

            # エラーログを保存
            if logs_dir and genre_safe and audience_safe and timestamp:
                parse_error_log = {
                    "timestamp": timestamp,
                    "error_type": "XML_ParseError",
                    "error_message": str(parse_error),
                    "xml_content": clean_xml
                }
                parse_error_filename = f"xml_parse_error_{genre_safe}_{audience_safe}_{timestamp}.json"
                parse_error_file_path = logs_dir / parse_error_filename
                with open(parse_error_file_path, 'w', encoding='utf-8') as f:
                    json.dump(parse_error_log, f, ensure_ascii=False, indent=2)

            # 自動解析を試行
            qa_pairs = parse_qa_from_text_fallback(clean_xml)

            # 自動解析でも失敗した場合のフォールバック
            if not qa_pairs:
                console.print("[yellow]自動解析も失敗したため、テキストから直接Q&Aを抽出します...[/yellow]")
                qa_pairs = _extract_qa_from_fallback_text(cleaned_content)

    if not qa_pairs:
        console.print(f"[bold red]LLMが生成したXMLの解析に失敗しました[/bold red]")
        console.print(f"[dim]受信したテキスト: {cleaned_content[:500]}...[/dim]")

        # 解析失敗のログを保存
        if logs_dir and genre_safe and audience_safe and timestamp:
            failure_log = {
                "timestamp": timestamp,
                "failure_reason": "XML解析失敗",
                "original_content": xml_content[:1000],
                "cleaned_content": cleaned_content[:1000]
            }
            failure_filename = f"xml_parse_failure_{genre_safe}_{audience_safe}_{timestamp}.json"
            failure_file_path = logs_dir / failure_filename
            with open(failure_file_path, 'w', encoding='utf-8') as f:
                json.dump(failure_log, f, ensure_ascii=False, indent=2)

    return qa_pairs


def _clean_llm_response(response: str) -> str:
    """LLMからのレスポンスをクリーンアップする"""
    import re

    # 不要なテキストを除去
    cleaned = response

    # ```xml ... ``` のようなコードブロックを除去
    cleaned = re.sub(r'```xml\s*|\s*```', '', cleaned, flags=re.IGNORECASE)

    # ``` ... ``` のようなコードブロックを除去
    cleaned = re.sub(r'```\s*|\s*```', '', cleaned)

    # <xml> ... </xml> のようなタグを除去
    cleaned = re.sub(r'<xml>\s*|\s*</xml>', '', cleaned, flags=re.IGNORECASE)

    # 不要な空白や改行を整理
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    return cleaned


def _extract_qa_from_fallback_text(text: str) -> List[Dict[str, str]]:
    """テキストから直接Q&Aを抽出するフォールバック関数"""
    qa_pairs = []

    try:
        # <Question>と<Answer>タグで分割
        import re

        # Questionタグを検索
        question_pattern = r'<Question>(.*?)</Question>'
        answer_pattern = r'<Answer>(.*?)</Answer>'

        questions = re.findall(question_pattern, text, re.DOTALL)
        answers = re.findall(answer_pattern, text, re.DOTALL)

        # 同じ数の質問と回答がある場合のみペアを作成
        min_count = min(len(questions), len(answers))
        for i in range(min_count):
            qa_pairs.append({
                "question": _decode_xml_entities(questions[i].strip()),
                "answer": _decode_xml_entities(answers[i].strip())
            })

    except Exception as e:
        console.print(f"[red]フォールバック解析も失敗:[/red] {e}")

    return qa_pairs


def _decode_xml_entities(text: str) -> str:
    """XMLエンティティをデコードする（シンプル版）"""
    import html
    if text:
        return html.unescape(text)
    return text


def _save_qa_pairs_to_xml(qa_pairs: List[Dict[str, str]], logs_dir: Path, qa_filename: str) -> None:
    """Q&Aペアをきれいに整形されたXMLファイルとして保存（サブエレメント方式）"""
    if not qa_pairs or not logs_dir:
        return

    qa_file_path = logs_dir / qa_filename

    # ElementTreeで構造化生成
    root = ET.Element("QAPairs")
    for qa in qa_pairs:
        pair_elem = ET.SubElement(root, "Pair")
        question_elem = ET.SubElement(pair_elem, "Question")
        question_elem.text = qa["question"]

        answer_elem = ET.SubElement(pair_elem, "Answer")

        # 回答内容を解析
        parsed_answer = _parse_answer_with_think(qa["answer"])

        if parsed_answer["has_think"]:
            # <think>をサブエレメントとして追加
            think_elem = ET.SubElement(answer_elem, "think")
            think_elem.text = parsed_answer["think_content"]
            think_elem.tail = parsed_answer["answer_content"]
        else:
            # 通常の回答
            answer_elem.text = parsed_answer["answer_content"]

    # 整形して保存
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")

    qa_file_path.write_text(pretty_xml, encoding='utf-8')
    console.print(f"[green]✓[/green] QAペアを保存: {qa_filename} ({len(qa_pairs)}件)")


def _parse_answer_with_think(answer_text: str) -> Dict[str, str]:
    """<think>タグを含む回答をパースして分離"""
    import re

    # <think>...</think>タグを検索
    think_match = re.search(r'<think>(.*?)</think>', answer_text, re.DOTALL)

    if think_match:
        think_content = think_match.group(1).strip()
        # <think>タグ以降の回答テキストを取得
        answer_content = answer_text[think_match.end():].strip()
        return {
            "has_think": True,
            "think_content": think_content,
            "answer_content": answer_content
        }
    else:
        return {
            "has_think": False,
            "think_content": "",
            "answer_content": answer_text
        }
