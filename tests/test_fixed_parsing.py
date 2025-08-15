#!/usr/bin/env python3
"""修正されたAnswer解析のテスト"""

import xml.etree.ElementTree as ET

def test_fixed_answer_parsing():
    """修正されたAnswer解析をテスト"""
    
    # テストXML（実際のファイルと同じ構造）
    xml_content = """<QAPairs>
    <Pair>
        <Question>テスト質問1</Question>
        <Answer>
            <think>これは思考プロセスです</think>
            これは回答内容です。
        </Answer>
    </Pair>
    <Pair>
        <Question>テスト質問2</Question>
        <Answer>普通の回答です。</Answer>
    </Pair>
</QAPairs>"""
    
    root = ET.fromstring(xml_content)
    
    for i, pair_node in enumerate(root.findall('Pair'), 1):
        question_node = pair_node.find('Question')
        answer_node = pair_node.find('Answer')
        
        if question_node is not None and answer_node is not None:
            question_text = question_node.text or ""
            
            print(f"=== Pair {i} ===")
            print(f"質問: {question_text.strip()}")
            print(f"Answer要素の子要素数: {len(answer_node)}")
            
            # <Answer>要素内の内容を適切に取得
            if len(answer_node) > 0:
                # サブエレメントがある場合（<think>タグなど）
                answer_parts = []
                
                # Answer要素の直接のテキスト（<think>より前）
                if answer_node.text:
                    answer_parts.append(answer_node.text.strip())
                    print(f"Answer.text: '{answer_node.text.strip()}'")
                
                # 各サブエレメントのtail（サブエレメントの後のテキスト）
                for child in answer_node:
                    print(f"子要素: tag='{child.tag}', text='{child.text}', tail='{child.tail}'")
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
            
            print(f"最終的な回答: '{answer_text}'")
            print()

if __name__ == "__main__":
    test_fixed_answer_parsing()
