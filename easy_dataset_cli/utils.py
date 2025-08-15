# easy_dataset_cli/utils.py
"""ユーティリティ関数"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from typing import List, Dict
from .core import parse_ga_markdown_fallback


def convert_markdown_ga_to_xml(markdown_file: Path, xml_file: Path) -> None:
    """マークダウン形式のGA定義ファイルをXML形式に変換する"""
    text = markdown_file.read_text(encoding="utf-8")
    ga_pairs = parse_ga_markdown_fallback(text)
    
    if not ga_pairs:
        raise ValueError("有効なGAペアが見つかりませんでした")
    
    # XMLを構築
    root = ET.Element("GADefinitions")
    
    for pair in ga_pairs:
        pair_elem = ET.SubElement(root, "Pair")
        
        genre_elem = ET.SubElement(pair_elem, "Genre")
        genre_title_elem = ET.SubElement(genre_elem, "Title")
        genre_title_elem.text = pair['genre']['title']
        genre_desc_elem = ET.SubElement(genre_elem, "Description")
        genre_desc_elem.text = pair['genre']['description']
        
        audience_elem = ET.SubElement(pair_elem, "Audience")
        audience_title_elem = ET.SubElement(audience_elem, "Title")
        audience_title_elem.text = pair['audience']['title']
        audience_desc_elem = ET.SubElement(audience_elem, "Description")
        audience_desc_elem.text = pair['audience']['description']
    
    # 整形されたXMLとして保存
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    xml_content = reparsed.toprettyxml(indent="  ")
    
    xml_file.write_text(xml_content, encoding="utf-8")