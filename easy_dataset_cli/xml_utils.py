# easy_dataset_cli/xml_utils.py
"""XML処理関連のユーティリティ"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from collections import defaultdict
from typing import List, Dict
from pathlib import Path
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


def load_existing_xml_file(xml_file_path: Path) -> List[Dict[str, str]]:
    """既存のXMLファイルからQ&Aペアを読み込む"""
    qa_pairs = []
    
    try:
        if not xml_file_path.exists():
            return qa_pairs
            
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        genre = root.get('genre', 'Unknown')
        
        for pair in root.findall('Pair'):
            audience_elem = pair.find('Audience')
            question_elem = pair.find('Question')
            answer_elem = pair.find('Answer')
            
            if all([audience_elem is not None, question_elem is not None, answer_elem is not None]):
                qa_pairs.append({
                    "genre": genre,
                    "audience": audience_elem.text or "",
                    "question": question_elem.text or "",
                    "answer": answer_elem.text or ""
                })
                
    except Exception as e:
        console.print(f"[yellow]既存XMLファイルの読み込みに失敗: {e}[/yellow]")
    
    return qa_pairs


def load_existing_xml_file_with_fallback(xml_file_path: Path, genre_from_filename: str = None) -> List[Dict[str, str]]:
    """既存のXMLファイルからQ&Aペアを読み込み、ファイル名からジャンル情報を取得するフォールバック関数"""
    qa_pairs = []
    
    try:
        if not xml_file_path.exists():
            return qa_pairs
            
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        # XML内のgenre属性を優先し、なければファイル名から取得した情報を使用
        genre = root.get('genre', genre_from_filename or 'Unknown')
        
        for pair in root.findall('Pair'):
            audience_elem = pair.find('Audience')
            question_elem = pair.find('Question')
            answer_elem = pair.find('Answer')
            
            # Audience要素がない場合は、ファイル名から取得したAudience情報を使用
            if audience_elem is None:
                # ファイル名からAudience情報を取得（この関数の呼び出し元で設定済み）
                audience = genre_from_filename.split('_')[-1] if genre_from_filename and '_' in genre_from_filename else ""
            else:
                audience = audience_elem.text or ""
            
            if question_elem is not None and answer_elem is not None:
                qa_pairs.append({
                    "genre": genre,
                    "audience": audience,
                    "question": question_elem.text or "",
                    "answer": answer_elem.text or ""
                })
                
    except Exception as e:
        console.print(f"[yellow]既存XMLファイルの読み込みに失敗: {e}[/yellow]")
    
    return qa_pairs


def aggregate_logs_xml_to_qa(logs_dir: Path, qa_dir: Path) -> None:
    """logsフォルダ内のXMLファイルを集約してqaフォルダの既存XMLファイルを更新・追加する"""
    from rich.console import Console
    
    console = Console()
    
    console.print(f"[bold blue]logsフォルダからXMLファイルを集約して既存ファイルを更新しています...[/bold blue]")
    
    # qaディレクトリが存在しない場合は作成
    qa_dir.mkdir(parents=True, exist_ok=True)
    
    # logsディレクトリ内のXMLファイルを検索
    xml_files = list(logs_dir.glob("*.xml"))
    
    if not xml_files:
        console.print(f"[yellow]logsフォルダにXMLファイルが見つかりません: {logs_dir}[/yellow]")
        return
    
    console.print(f"[dim]{len(xml_files)}個のXMLファイルを検出[/dim]")
    
    # GenreごとにQ&Aペアを集約
    genre_qa_pairs = defaultdict(list)
    
    for xml_file in xml_files:
        try:
            console.print(f"[dim]処理中: {xml_file.name}[/dim]")
            
            # ファイル名からGenre情報を抽出（例: qa_pairs_FAQ_初心者ゲーマー_20250815_171008.xml）
            filename = xml_file.stem
            if filename.startswith("qa_pairs_"):
                # GenreとAudience情報を抽出
                parts = filename.replace("qa_pairs_", "").split("_")
                if len(parts) >= 3:  # genre + audience + timestamp + timestamp
                    genre = parts[0]
                    # 残りの部分はAudience（_で区切られている可能性がある）
                    # 最後の2要素はタイムスタンプなので除外
                    audience = "_".join(parts[1:-2])
                    
                    console.print(f"[dim]ファイル名解析: genre={genre}, audience={audience}[/dim]")
                    
                    # XMLファイルからQ&Aペアを読み込む（ファイル名からジャンル情報を渡す）
                    qa_pairs = load_existing_xml_file_with_fallback(xml_file, genre)
                    
                    console.print(f"[dim]読み込んだQ&Aペア数: {len(qa_pairs)}[/dim]")
                    
                    # Genre情報を付与して保存
                    for qa_pair in qa_pairs:
                        qa_pair["genre"] = genre
                        qa_pair["audience"] = audience
                        genre_qa_pairs[genre].append(qa_pair)
                else:
                    console.print(f"[yellow]ファイル名の解析に失敗: {filename}[/yellow]")
                        
        except Exception as e:
            console.print(f"[yellow]ファイルの処理中にエラー: {xml_file.name} - {e}[/yellow]")
            continue
    
    # Genreごとに既存XMLファイルを更新
    console.print(f"\n[bold green]集約結果:[/bold green]")
    total_updated = 0
    
    for genre, qa_pairs in genre_qa_pairs.items():
        console.print(f"  - [cyan]{genre}[/cyan]: {len(qa_pairs)}件のQ&Aを追加")
        
        # 既存のXMLファイルを検索
        safe_genre_name = "".join(c for c in genre if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
        existing_file = qa_dir / f"{safe_genre_name}.xml"
        
        # 既存のQ&Aペアを読み込む（ファイルが存在する場合）
        existing_pairs = []
        if existing_file.exists():
            existing_pairs = load_existing_xml_file(existing_file)
            console.print(f"    [dim]既存の{len(existing_pairs)}件のQ&Aを読み込み[/dim]")
        
        # 新しいQ&Aを追加（重複を避ける）
        existing_questions = {pair["question"] for pair in existing_pairs}
        new_pairs = []
        for pair in qa_pairs:
            if pair["question"] not in existing_questions:
                new_pairs.append(pair)
            else:
                console.print(f"    [yellow]重複するQ&Aをスキップ: {pair['question'][:50]}...[/yellow]")
        
        console.print(f"    [green]追加する新しいQ&A: {len(new_pairs)}件[/green]")
        
        # 既存のペアに新しいペアを追加
        updated_pairs = existing_pairs + new_pairs
        
        if updated_pairs:
            # XMLに変換
            root = ET.Element("QAPairs")
            root.set("genre", genre)

            for item in updated_pairs:
                pair_elem = ET.SubElement(root, "Pair")

                audience_elem = ET.SubElement(pair_elem, "Audience")
                audience_elem.text = item["audience"]

                question_elem = ET.SubElement(pair_elem, "Question")
                question_elem.text = item["question"]

                answer_elem = ET.SubElement(pair_elem, "Answer")
                answer_elem.text = item["answer"]

            # 整形して保存
            rough_string = ET.tostring(root, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            xml_content = reparsed.toprettyxml(indent="  ")
            
            existing_file.write_text(xml_content, encoding='utf-8')
            console.print(f"    [green]✓[/green] {existing_file.name} を更新 ({len(updated_pairs)}件)")
            total_updated += 1
        else:
            console.print(f"    [yellow]更新するQ&Aがありません[/yellow]")
    
    console.print(f"\n[bold green]✓[/bold green] 合計{total_updated}個のジャンルのXMLファイルを更新しました")


def convert_to_xml_by_genre(all_qa_pairs: List[Dict[str, str]], qa_dir: Path = None, append_mode: bool = False) -> Dict[str, str]:
    """Q&AペアのリストをGenreごとにグループ化し、整形されたXML文字列の辞書に変換する
    
    Args:
        all_qa_pairs: 変換するQ&Aペアのリスト
        qa_dir: QAファイルが保存されているディレクトリ（追加モードの場合に必要）
        append_mode: 既存ファイルに追加するかどうか
    """
    grouped_by_genre = defaultdict(list)

    for item in all_qa_pairs:
        grouped_by_genre[item["genre"]].append(item)

    xml_outputs = {}
    
    for genre, pairs in grouped_by_genre.items():
        # 追加モードの場合は既存のXMLファイルを読み込む
        if append_mode and qa_dir:
            safe_genre_name = "".join(c for c in genre if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
            existing_file = qa_dir / f"{safe_genre_name}.xml"
            
            if existing_file.exists():
                existing_pairs = load_existing_xml_file(existing_file)
                console.print(f"[dim]Genre '{genre}': 既存の{len(existing_pairs)}件のQ&Aを読み込みました[/dim]")
                # 既存のペアを先頭に追加
                pairs = existing_pairs + pairs
        
        root = ET.Element("QAPairs")
        root.set("genre", genre)

        for item in pairs:
            pair_elem = ET.SubElement(root, "Pair")

            audience_elem = ET.SubElement(pair_elem, "Audience")
            audience_elem.text = item["audience"]

            question_elem = ET.SubElement(pair_elem, "Question")
            question_elem.text = item["question"]

            answer_elem = ET.SubElement(pair_elem, "Answer")
            
            # 回答内容を解析
            parsed_answer = _parse_answer_with_think(item["answer"])
            
            if parsed_answer["has_think"]:
                # <think>をサブエレメントとして追加
                think_elem = ET.SubElement(answer_elem, "think")
                think_elem.text = parsed_answer["think_content"]
                think_elem.tail = parsed_answer["answer_content"]
            else:
                # 通常の回答
                answer_elem.text = parsed_answer["answer_content"]

        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        xml_output = reparsed.toprettyxml(indent="  ")
        
        xml_outputs[genre] = xml_output

    return xml_outputs
