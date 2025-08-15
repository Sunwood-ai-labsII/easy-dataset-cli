#!/usr/bin/env python3
"""ElementTreeでthinkタグを保持するテスト"""

def test_elementtree_with_cdata():
    """ElementTreeでCDATAセクションを使ってthinkタグを保持"""
    
    import xml.etree.ElementTree as ET
    from xml.dom import minidom
    
    # サンプルデータ
    qa_pairs = [
        {
            "question": "テスト質問1",
            "answer": "<think>これは思考プロセスです</think>これはテスト回答1です。"
        },
        {
            "question": "テスト質問2", 
            "answer": "<think>別の思考プロセス</think>これはテスト回答2です。"
        }
    ]
    
    print("方法1: 単純な文字列置換")
    # 方法1: ElementTreeで生成後、文字列置換
    root = ET.Element("QAPairs")
    for qa in qa_pairs:
        pair_elem = ET.SubElement(root, "Pair")
        question_elem = ET.SubElement(pair_elem, "Question")
        question_elem.text = qa["question"]
        answer_elem = ET.SubElement(pair_elem, "Answer")
        answer_elem.text = qa["answer"]
    
    # 整形
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # 単純な置換でthinkタグを復元
    pretty_xml = pretty_xml.replace("&lt;think&gt;", "<think>")
    pretty_xml = pretty_xml.replace("&lt;/think&gt;", "</think>")
    
    print(pretty_xml)
    
    print("\n方法2: ET.toustring後に置換")
    # 方法2: ET.tostringの結果を直接操作
    xml_string = ET.tostring(root, encoding='unicode')
    xml_string = xml_string.replace("&lt;think&gt;", "<think>")
    xml_string = xml_string.replace("&lt;/think&gt;", "</think>")
    
    # 手動で整形
    import xml.dom.minidom
    dom = xml.dom.minidom.parseString(xml_string)
    pretty_xml2 = dom.toprettyxml(indent="  ")
    
    print(pretty_xml2)
    
    # <think>タグがエスケープされているかチェック
    if "&lt;think&gt;" in pretty_xml:
        print("❌ 方法1: <think>タグがエスケープされています!")
    else:
        print("✅ 方法1: <think>タグはエスケープされていません!")
        
    if "&lt;think&gt;" in pretty_xml2:
        print("❌ 方法2: <think>タグがエスケープされています!")
    else:
        print("✅ 方法2: <think>タグはエスケープされていません!")

if __name__ == "__main__":
    test_elementtree_with_cdata()
