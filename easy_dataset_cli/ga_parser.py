# easy_dataset_cli/ga_parser.py
"""GA定義の解析関連機能"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict
import mistune
from rich.console import Console

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
        console.print("[yellow]自動解析を試行中...[/yellow]")
        from .xml_utils import parse_ga_from_text_fallback
        pairs = parse_ga_from_text_fallback(xml_content)

    except Exception as e:
        console.print(f"[bold red]予期しないエラー:[/bold red] {e}")

    return pairs
