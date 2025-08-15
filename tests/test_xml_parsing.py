#!/usr/bin/env python3
"""XMLパース改善のテストスクリプト"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'easy_dataset_cli'))

from easy_dataset_cli.qa_generator import _parse_qa_response, _clean_llm_response
from pathlib import Path
import json

def test_xml_parsing():
    """XMLパースのテスト"""
    
    # テストケース1: 正常なXML
    test_xml_1 = '''<QAPairs>
<Pair>
<Question>テスト質問1</Question>
<Answer>テスト回答1</Answer>
</Pair>
<Pair>
<Question>テスト質問2</Question>
<Answer>テスト回答2</Answer>
</Pair>
</QAPairs>'''
    
    # テストケース2: バッククォート付きのXML（エラーの原因）
    test_xml_2 = '''```xml
<QAPairs>
<Pair>
<Question>東方地霊殿はどんなジャンルのゲームですか？</Question>
<Answer>弾幕系シューティングゲームで、横スクロールの弾幕を回避しながら敵を倒すタイプです。</Answer>
</Pair>
<Pair>
<Question>このゲームはどのOSでプレイできますか？</Question>
<Answer>Windows 2000、XP、Vista以降のPCで動作し、2020年にはSteam版も配信されています。</Answer>
</Pair>
<Pair>
<Question>最低動作環境は何ですか？</Question>
<Answer>CPUは1GHz以上のPentium、DirectX 9.0以上、メモリ256 MB、HDD空き容量600 MBが必要です。</Answer>
</Pair>
<Pair>
<Question>インストール手順は簡単ですか？</Question>
<Answer>Steam版ならアカウントにログインして「購入」→「インストール」ボタンを押すだけで自動インストールされます。</Answer>
</Pair>
</QAPairs>
```'''
    
    # テストケース3: <Pair>タグのみのXML
    test_xml_3 = '''<Pair>
<Question>Pairタグのみの質問1</Question>
<Answer>Pairタグのみの回答1</Answer>
</Pair>
<Pair>
<Question>Pairタグのみの質問2</Question>
<Answer>Pairタグのみの回答2</Answer>
</Pair>'''
    
    # テストケース4: 不完全なXML
    test_xml_4 = '''<QAPairs>
<Pair>
<Question>不完全なXMLの質問</Question>
<Answer>不完全なXMLの回答</Answer>
</Pair>
<QAPairs>'''
    
    print("=== XMLパース改善テスト ===\n")
    
    # テストケース1
    print("テストケース1: 正常なXML")
    result1 = _parse_qa_response(test_xml_1, None, None, None, None)
    print(f"結果: {len(result1)}件のQ&Aを抽出")
    for i, qa in enumerate(result1, 1):
        print(f"  {i}. Q: {qa['question']}")
        print(f"     A: {qa['answer']}")
    print()
    
    # テストケース2
    print("テストケース2: バッククォート付きのXML（元のエラー）")
    result2 = _parse_qa_response(test_xml_2, None, None, None, None)
    print(f"結果: {len(result2)}件のQ&Aを抽出")
    for i, qa in enumerate(result2, 1):
        print(f"  {i}. Q: {qa['question']}")
        print(f"     A: {qa['answer']}")
    print()
    
    # テストケース3
    print("テストケース3: <Pair>タグのみのXML")
    result3 = _parse_qa_response(test_xml_3, None, None, None, None)
    print(f"結果: {len(result3)}件のQ&Aを抽出")
    for i, qa in enumerate(result3, 1):
        print(f"  {i}. Q: {qa['question']}")
        print(f"     A: {qa['answer']}")
    print()
    
    # テストケース4
    print("テストケース4: 不完全なXML")
    result4 = _parse_qa_response(test_xml_4, None, None, None, None)
    print(f"結果: {len(result4)}件のQ&Aを抽出")
    for i, qa in enumerate(result4, 1):
        print(f"  {i}. Q: {qa['question']}")
        print(f"     A: {qa['answer']}")
    print()
    
    # クリーニング機能のテスト
    print("=== クリーニング機能テスト ===")
    cleaned = _clean_llm_response(test_xml_2)
    print("クリーニング前:")
    print(test_xml_2[:200] + "...")
    print("\nクリーニング後:")
    print(cleaned[:200] + "...")
    
    return len(result1) > 0 and len(result2) > 0 and len(result3) > 0

if __name__ == "__main__":
    success = test_xml_parsing()
    if success:
        print("\n✅ すべてのテストが成功しました！")
    else:
        print("\n❌ テストに失敗しました。")
    sys.exit(0 if success else 1)
