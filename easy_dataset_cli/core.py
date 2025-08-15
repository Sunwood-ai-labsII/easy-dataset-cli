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

from .prompts import get_qa_generation_prompt, get_ga_definition_generation_prompt

# .envファイルを読み込む
load_dotenv()

console = Console()


def parse_ga_file(file_path: Path) -> List[Dict[str, Dict[str, str]]]:
    """XMLファイルからGAペアのリストを解析する"""
    text = file_path.read_text(encoding="utf-8")
    pairs = []
    console.print(f"[dim]GAファイルを読み込み中: {file_path}[/dim]")
    console.print(f"[dim]ファイル内容長: {len(text)} 文字[/dim]")
    
    try:
        # XMLから<GADefinitions>部分を抽出
        xml_start = text.find("<GADefinitions>")
        xml_end = text.rfind("</GADefinitions>")
        console.print(f"[dim]XML開始位置: {xml_start}, 終了位置: {xml_end}[/dim]")
        
        if xml_start != -1 and xml_end != -1:
            clean_xml = text[xml_start: xml_end + len("</GADefinitions>")]
            console.print(f"[dim]抽出されたXML長: {len(clean_xml)} 文字[/dim]")
            
            root = ET.fromstring(clean_xml)
            pair_nodes = root.findall('Pair')
            console.print(f"[dim]見つかったPairノード数: {len(pair_nodes)}[/dim]")
            
            for i, pair_node in enumerate(pair_nodes):
                genre_node = pair_node.find('Genre')
                audience_node = pair_node.find('Audience')
                
                if genre_node is not None and audience_node is not None:
                    genre_title_node = genre_node.find('Title')
                    genre_desc_node = genre_node.find('Description')
                    audience_title_node = audience_node.find('Title')
                    audience_desc_node = audience_node.find('Description')
                    
                    has_all = all([
                        genre_title_node is not None and genre_title_node.text and genre_title_node.text.strip(),
                        genre_desc_node is not None and genre_desc_node.text and genre_desc_node.text.strip(),
                        audience_title_node is not None and audience_title_node.text and audience_title_node.text.strip(),
                        audience_desc_node is not None and audience_desc_node.text and audience_desc_node.text.strip()
                    ])
                    
                    console.print(f"[dim]Pair {i+1}: {'✓' if has_all else '✗'} {genre_title_node.text if genre_title_node is not None else 'None'}[/dim]")
                    
                    if has_all:
                        pairs.append({
                            "genre": {
                                "title": genre_title_node.text.strip(),
                                "description": genre_desc_node.text.strip()
                            },
                            "audience": {
                                "title": audience_title_node.text.strip(),
                                "description": audience_desc_node.text.strip()
                            }
                        })
        
        # XMLが見つからない場合は従来のマークダウン形式で解析を試行
        if not pairs:
            console.print("[yellow]XMLからペアが見つからないため、マークダウン形式で再試行[/yellow]")
            pairs = parse_ga_markdown_fallback(text)
            
    except ET.ParseError as e:
        console.print(f"[yellow]XML解析エラー: {e}[/yellow]")
        # XML解析に失敗した場合はマークダウン形式で解析を試行
        pairs = parse_ga_markdown_fallback(text)
    
    console.print(f"[dim]最終的に解析されたペア数: {len(pairs)}[/dim]")
    return pairs


def parse_ga_markdown_fallback(text: str) -> List[Dict[str, Dict[str, str]]]:
    """マークダウンファイルからGAペアのリストを解析する（フォールバック）"""
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
    chunk: str, model: str, ga_pair: Dict[str, Dict[str, str]], logs_dir: Path = None, num_qa_pairs: int = None
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
                console.print(f"[yellow]XMLパースエラー、手動解析を試行中...[/yellow]")
                qa_pairs = parse_qa_from_text_fallback(clean_xml)

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


def parse_ga_definitions_from_xml(xml_content: str) -> List[Dict[str, Dict[str, str]]]:
    """XML形式のGA定義からGAペアのリストを解析する"""
    pairs = []
    
    try:
        # XMLタグから<GADefinitions>部分を抽出（マークダウンコードブロックを無視）
        xml_start = xml_content.find("<GADefinitions>")
        xml_end = xml_content.rfind("</GADefinitions>")
        
        if xml_start != -1 and xml_end != -1:
            clean_xml = xml_content[xml_start: xml_end + len("</GADefinitions>")]
            
            # XMLの特殊文字をエスケープ
            import html
            clean_xml = html.unescape(clean_xml)
            
            root = ET.fromstring(clean_xml)
            pair_nodes = root.findall('Pair')
            console.print(f"[dim]見つかったPairノード数: {len(pair_nodes)}[/dim]")
            
            for i, pair_node in enumerate(pair_nodes):
                genre_node = pair_node.find('Genre')
                audience_node = pair_node.find('Audience')
                
                if genre_node is not None and audience_node is not None:
                    genre_title_node = genre_node.find('Title')
                    genre_desc_node = genre_node.find('Description')
                    audience_title_node = audience_node.find('Title')
                    audience_desc_node = audience_node.find('Description')
                    
                    # より詳細なチェック
                    has_genre_title = genre_title_node is not None and genre_title_node.text and genre_title_node.text.strip()
                    has_genre_desc = genre_desc_node is not None and genre_desc_node.text and genre_desc_node.text.strip()
                    has_audience_title = audience_title_node is not None and audience_title_node.text and audience_title_node.text.strip()
                    has_audience_desc = audience_desc_node is not None and audience_desc_node.text and audience_desc_node.text.strip()
                    
                    if all([has_genre_title, has_genre_desc, has_audience_title, has_audience_desc]):
                        pairs.append({
                            "genre": {
                                "title": genre_title_node.text.strip(),
                                "description": genre_desc_node.text.strip()
                            },
                            "audience": {
                                "title": audience_title_node.text.strip(),
                                "description": audience_desc_node.text.strip()
                            }
                        })
                        console.print(f"[green]✓[/green] {genre_title_node.text.strip()} x {audience_title_node.text.strip()}")
                    else:
                        console.print(f"[yellow]⚠[/yellow] Pair {i+1}: 必要な要素が不足")
                else:
                    console.print(f"[yellow]⚠[/yellow] Pair {i+1}: GenreまたはAudienceノードが見つからない")
        else:
            console.print("[yellow]GADefinitionsタグが見つかりませんでした[/yellow]")
                        
    except ET.ParseError as parse_error:
        console.print(f"[bold red]GA定義XMLの解析に失敗しました:[/bold red] {parse_error}")
        console.print(f"[dim]問題のあるXML: {xml_content[xml_start:xml_start+200] if xml_start != -1 else xml_content[:200]}...[/dim]")
        
        # XMLエラーの場合、手動でテキスト解析を試行
        console.print("[yellow]手動解析を試行中...[/yellow]")
        pairs = parse_ga_from_text_fallback(xml_content)
        
    except Exception as e:
        console.print(f"[bold red]予期しないエラー:[/bold red] {e}")
    
    return pairs


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
                console.print(f"[green]✓[/green] (手動解析) {genre_title} x {audience_title}")
    
    except Exception as e:
        console.print(f"[red]手動解析も失敗:[/red] {e}")
    
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
                console.print(f"[green]✓[/green] (手動解析) Q&A追加")
    
    except Exception as e:
        console.print(f"[red]Q&A手動解析も失敗:[/red] {e}")
    
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
