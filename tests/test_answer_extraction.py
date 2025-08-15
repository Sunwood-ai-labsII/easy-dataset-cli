#!/usr/bin/env python3
"""Answer要素の内容取得テスト"""

import xml.etree.ElementTree as ET

def test_answer_content_extraction():
    """Answer要素の内容取得をテスト"""
    
    # テストXML
    xml_content = """<QAPairs>
    <Pair>
        <Question>テスト質問1</Question>
        <Answer><think>思考プロセス</think>回答内容</Answer>
    </Pair>
    <Pair>
        <Question>テスト質問2</Question>
        <Answer>普通の回答</Answer>
    </Pair>
</QAPairs>"""
    
    root = ET.fromstring(xml_content)
    
    for pair_node in root.findall('Pair'):
        question_node = pair_node.find('Question')
        answer_node = pair_node.find('Answer')
        
        if question_node is not None and answer_node is not None:
            question_text = question_node.text or ""
            
            print(f"質問: {question_text}")
            print(f"Answer要素の子要素数: {len(answer_node)}")
            print(f"Answer.text: '{answer_node.text}'")
            print(f"Answer.tail: '{answer_node.tail}'")
            
            # サブエレメントがある場合の詳細確認
            if len(answer_node) > 0:
                for i, child in enumerate(answer_node):
                    print(f"  子要素{i}: tag='{child.tag}', text='{child.text}', tail='{child.tail}'")
            
            # <Answer>要素内の全ての内容を取得（サブエレメント含む）
            if len(answer_node) > 0:
                # サブエレメントがある場合、XML文字列として再構築
                answer_content = ET.tostring(answer_node, encoding='unicode', method='xml')
                print(f"Answer XML: {answer_content}")
                # <Answer>タグを除去して内容のみ取得
                answer_text = answer_content[answer_content.find('>')+1:answer_content.rfind('<')]
                print(f"抽出された内容: '{answer_text}'")
            else:
                # サブエレメントがない場合は通常のテキスト
                answer_text = answer_node.text or ""
                print(f"通常テキスト: '{answer_text}'")
            
            print("---")

if __name__ == "__main__":
    test_answer_content_extraction()
