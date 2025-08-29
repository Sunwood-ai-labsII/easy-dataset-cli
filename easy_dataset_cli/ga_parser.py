# easy_dataset_cli/ga_parser.py
"""GA定義の解析関連機能"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict
import mistune
from rich.console import Console
import re

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
        console.print(f"[red]XML解析エラー: {e}[/red]")
        # XML解析に失敗した場合は改良版を試行
        console.print("[yellow]改良版XML解析を試行中...[/yellow]")
        pairs = parse_ga_definitions_from_xml_improved(text)

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
                header_text = "".join(child.get('text', '') for child in node['children'])
                if 'genre' in header_text.lower():
                    current_type = 'genre'
                    genre['title'] = header_text.replace('Genre:', '').strip()
                elif 'audience' in header_text.lower():
                    current_type = 'audience'
                    audience['title'] = header_text.replace('Audience:', '').strip()
            elif node['type'] == 'paragraph':
                description = "".join(child.get('text', '') for child in node['children'])
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


def parse_ga_definitions_from_xml_improved(xml_content: str) -> List[Dict[str, Dict[str, str]]]:
    """改良版: 正規表現を使い、コードブロックや不正なXMLを処理できるGA定義解析関数"""
    pairs = []
    console.print(f"[dim]XML解析開始: 内容長 {len(xml_content)} 文字[/dim]")

    try:
        # Step 1: 正規表現で<GADefinitions>ブロックを抽出
        # re.DOTALLフラグにより、改行文字を含む文字列全体を検索対象にする
        match = re.search(r"<GADefinitions>.*?</GADefinitions>", xml_content, re.DOTALL)

        if not match:
            console.print("[yellow]GADefinitionsタグで囲まれたXMLブロックが見つかりませんでした[/yellow]")
            console.print("[yellow]フォールバック解析を試行中...[/yellow]")
            return parse_ga_definitions_from_xml(xml_content)

        raw_xml = match.group(0)
        console.print(f"[dim]正規表現でXMLブロックを抽出完了: {len(raw_xml)} 文字[/dim]")

        # Step 2: XML宣言を追加
        if not raw_xml.startswith("<?xml"):
            raw_xml = '<?xml version="1.0" encoding="utf-8"?>\n' + raw_xml

        # Step 3: XML解析を実行
        root = ET.fromstring(raw_xml)
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

                # 有効なデータが存在するかチェック
                if all(node is not None and node.text and node.text.strip() for node in [genre_title_node, genre_desc_node, audience_title_node, audience_desc_node]):
                    genre_title = genre_title_node.text.strip()
                    audience_title = audience_title_node.text.strip()
                    pairs.append({
                        "genre": {
                            "title": genre_title,
                            "description": genre_desc_node.text.strip()
                        },
                        "audience": {
                            "title": audience_title,
                            "description": audience_desc_node.text.strip()
                        }
                    })
                    console.print(f"[green]✓[/green] {genre_title} x {audience_title}")
                else:
                    console.print(f"[yellow]⚠[/yellow] Pair {i+1}: 要素が空または無効")
            else:
                console.print(f"[yellow]⚠[/yellow] Pair {i+1}: GenreまたはAudienceノードが見つからない")

    except ET.ParseError as parse_error:
        console.print(f"[bold red]XML解析エラー:[/bold red] {parse_error}")
        console.print(f"[dim]パース失敗したXML内容: {raw_xml if 'raw_xml' in locals() else 'N/A'}[/dim]")
        console.print("[yellow]フォールバック解析を試行中...[/yellow]")
        return parse_ga_definitions_from_xml(xml_content)

    except Exception as e:
        console.print(f"[bold red]予期しないエラー:[/bold red] {e}")
        console.print("[yellow]フォールバック解析を試行中...[/yellow]")
        return parse_ga_definitions_from_xml(xml_content)

    console.print(f"[dim]最終的に解析されたペア数: {len(pairs)}[/dim]")
    return pairs
