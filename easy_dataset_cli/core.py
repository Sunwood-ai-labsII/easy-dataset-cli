# easy_dataset_cli/core.py
"""コアロジック: テキスト分割、Q&A生成、XML変換"""

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from collections import defaultdict
from pathlib import Path
from typing import List, Dict
import mistune
from langchain_text_splitters import RecursiveCharacterTextSplitter
from litellm import completion
from rich.console import Console
from dotenv import load_dotenv

from .prompts import QA_GENERATION_PROMPT_WITH_GA_JA, GA_DEFINITION_GENERATION_PROMPT_JA

# .envファイルを読み込む
load_dotenv()

console = Console()


def parse_ga_file(file_path: Path) -> List[Dict[str, Dict[str, str]]]:
    """マークダウンファイルからGAペアのリストを解析する"""
    text = file_path.read_text(encoding="utf-8")
    pairs = []
    sections = text.split('---')
    
    for section in sections:
        if not section.strip():
            continue

        ast = mistune.create_markdown(renderer=None)(section)
        genre = {"title": "", "description": ""}
        audience = {"title": "", "description": ""}
        current_type = None

        for node in ast:
            if node['type'] == 'heading':
                header_text = "".join(child['text'] for child in node['children'])
                if 'genre' in header_text.lower():
                    current_type = 'genre'
                    genre['title'] = header_text.replace('Genre:', '').strip()
                elif 'audience' in header_text.lower():
                    current_type = 'audience'
                    audience['title'] = header_text.replace('Audience:', '').strip()
            elif node['type'] == 'paragraph':
                description = "".join(child['text'] for child in node['children'])
                if current_type == 'genre':
                    genre['description'] = description
                elif current_type == 'audience':
                    audience['description'] = description

        if genre['title'] and audience['title']:
            pairs.append({"genre": genre, "audience": audience})
    
    return pairs


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """LangChainのTextSplitterを使ってテキストをチャンクに分割する"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    docs = text_splitter.create_documents([text])
    return [doc.page_content for doc in docs]


def generate_qa_for_chunk_with_ga(
    chunk: str, model: str, ga_pair: Dict[str, Dict[str, str]]
) -> List[Dict[str, str]]:
    """litellmを使い、1つのチャンクと1つのGAペアからQ&Aペアのリストを生成する"""
    prompt = QA_GENERATION_PROMPT_WITH_GA_JA.format(
        context=chunk,
        genre_title=ga_pair['genre']['title'],
        genre_description=ga_pair['genre']['description'],
        audience_title=ga_pair['audience']['title'],
        audience_description=ga_pair['audience']['description'],
    )

    messages = [
        {"role": "system", "content": "あなたは、XML形式で厳密に出力する優秀なアシスタントです。"},
        {"role": "user", "content": prompt}
    ]

    # OpenRouter用の環境変数設定
    os.environ["OPENROUTER_API_KEY"] = os.getenv("OPENROUTER_API_KEY", "")
    
    try:
        response = completion(model=model, messages=messages)
        xml_content = response.choices[0].message.content
        qa_pairs = []

        # LLMからの出力には余分なテキストが含まれることがあるため、XML部分のみを抽出
        xml_start = xml_content.find("<QAPairs>")
        xml_end = xml_content.rfind("</QAPairs>")

        if xml_start != -1 and xml_end != -1:
            clean_xml = xml_content[xml_start: xml_end + len("</QAPairs>")]
            root = ET.fromstring(clean_xml)

            for pair_node in root.findall('Pair'):
                question_node = pair_node.find('Question')
                answer_node = pair_node.find('Answer')

                if question_node is not None and answer_node is not None:
                    qa_pairs.append({
                        "question": question_node.text or "",
                        "answer": answer_node.text or ""
                    })

        return qa_pairs

    except ET.ParseError as parse_error:
        console.print(
            f"[bold red]LLMが生成したXMLの解析に失敗しました:[/bold red] {parse_error}"
        )
        console.print(f"[dim]受信したテキスト: {xml_content[:200]}...[/dim]")
        return []
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


def generate_ga_definitions(text_content: str, model: str) -> str:
    """litellmを使い、元の文章からGAペア定義のマークダウンを生成する"""
    # LLMに渡すテキストは長すぎるとコストや性能に影響するため、先頭部分に限定する
    context = text_content[:8000]

    prompt = GA_DEFINITION_GENERATION_PROMPT_JA.format(context=context)

    messages = [
        {"role": "system", "content": "あなたは、Markdown形式で厳密に出力する優秀なアシスタントです。"},
        {"role": "user", "content": prompt}
    ]

    # OpenRouter用の環境変数設定
    os.environ["OPENROUTER_API_KEY"] = os.getenv("OPENROUTER_API_KEY", "")
    
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
        markdown_content = response.choices[0].message.content
        return markdown_content
    except Exception as error:
        console.print(f"[bold red]GA定義の生成中にエラーが発生しました:[/bold red] {error}")
        raise


def convert_to_xml_by_genre(all_qa_pairs: List[Dict[str, str]]) -> Dict[str, str]:
    """Q&AペアのリストをGenreごとにグループ化し、整形されたXML文字列の辞書に変換する"""
    grouped_by_genre = defaultdict(list)

    for item in all_qa_pairs:
        grouped_by_genre[item["genre"]].append(item)

    xml_outputs = {}
    for genre, pairs in grouped_by_genre.items():
        root = ET.Element("QAPairs")
        root.set("genre", genre)

        for item in pairs:
            pair_elem = ET.SubElement(root, "Pair")

            audience_elem = ET.SubElement(pair_elem, "Audience")
            audience_elem.text = item["audience"]

            question_elem = ET.SubElement(pair_elem, "Question")
            question_elem.text = item["question"]

            answer_elem = ET.SubElement(pair_elem, "Answer")
            answer_elem.text = item["answer"]

        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        xml_outputs[genre] = reparsed.toprettyxml(indent="  ")

    return xml_outputs