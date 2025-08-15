# easy_dataset_cli/xml_utils.py
"""XML処理関連のユーティリティ"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from collections import defaultdict
from typing import List, Dict
from rich.console import Console

console = Console()


def parse_ga_from_text_fallback(content: str) -> List[Dict[str, Dict[str, str]]]:
    """XMLパースに失敗した場合のフォールバック：テキストから直接解析"""
    pairs = []

    try:
        # <Pair>タグで分割
        pair_sections = content.split('<Pair>')

        for section in pair_sections[1:]:  # 最初の要素は空なのでスキップ
            if '</Pair>' not in section:
                continue

            pair_content = section.split('</Pair>')[0]

            # Title要素を抽出
            genre_title = extract_text_between_tags(pair_content, 'Genre', 'Title')
            genre_desc = extract_text_between_tags(pair_content, 'Genre', 'Description')
            audience_title = extract_text_between_tags(pair_content, 'Audience', 'Title')
            audience_desc = extract_text_between_tags(pair_content, 'Audience', 'Description')

            if all([genre_title, genre_desc, audience_title, audience_desc]):
                pairs.append({
                    "genre": {
                        "title": genre_title.strip(),
                        "description": genre_desc.strip()
                    },
                    "audience": {
                        "title": audience_title.strip(),
                        "description": audience_desc.strip()
                    }
                })
                console.print(f"[green]✓[/green] (自動解析) {genre_title} x {audience_title}")

    except Exception as e:
        console.print(f"[red]自動解析も失敗:[/red] {e}")

    return pairs


def extract_text_between_tags(content: str, parent_tag: str, child_tag: str) -> str:
    """指定されたタグ間のテキストを抽出"""
    try:
        # 親タグ内を探す
        parent_start = content.find(f'<{parent_tag}>')
        parent_end = content.find(f'</{parent_tag}>')

        if parent_start == -1 or parent_end == -1:
            return ""

        parent_content = content[parent_start:parent_end]

        # 子タグ内のテキストを抽出
        child_start = parent_content.find(f'<{child_tag}>')
        child_end = parent_content.find(f'</{child_tag}>')

        if child_start == -1 or child_end == -1:
            return ""

        return parent_content[child_start + len(f'<{child_tag}>'):child_end]

    except Exception:
        return ""


def parse_qa_from_text_fallback(content: str) -> List[Dict[str, str]]:
    """Q&A XMLパースに失敗した場合のフォールバック：テキストから直接解析"""
    qa_pairs = []

    try:
        # <Pair>タグで分割
        pair_sections = content.split('<Pair>')

        for section in pair_sections[1:]:  # 最初の要素は空なのでスキップ
            if '</Pair>' not in section:
                continue

            pair_content = section.split('</Pair>')[0]

            # Question と Answer を抽出
            question = extract_simple_tag_content(pair_content, 'Question')
            answer = extract_simple_tag_content(pair_content, 'Answer')

            if question and answer:
                qa_pairs.append({
                    "question": question.strip(),
                    "answer": answer.strip()
                })
                console.print("[green]✓[/green] (自動解析) Q&A追加")

    except Exception as e:
        console.print(f"[red]Q&A自動解析も失敗:[/red] {e}")

    return qa_pairs


def extract_simple_tag_content(content: str, tag: str) -> str:
    """シンプルなタグ内のテキストを抽出"""
    try:
        start_tag = f'<{tag}>'
        end_tag = f'</{tag}>'

        start_pos = content.find(start_tag)
        end_pos = content.find(end_tag)

        if start_pos == -1 or end_pos == -1:
            return ""

        return content[start_pos + len(start_tag):end_pos]

    except Exception:
        return ""


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
