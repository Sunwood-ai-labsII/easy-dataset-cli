#!/usr/bin/env python3
"""<think>タグのエスケープテスト"""

import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from easy_dataset_cli.qa_generator import _decode_xml_entities

def test_think_tag_preservation():
    """<think>タグが適切に保持されることをテスト"""
    
    # テストケース1: <think>タグを含む回答
    test_text1 = """<think>これはミトコンドリアの機能についての思考プロセスです。細胞のエネルギー工場として機能します。</think>ミトコンドリアは細胞のエネルギー通貨であるATPを生成する重要な細胞小器官です。"""
    
    result1 = _decode_xml_entities(test_text1)
    print("テストケース1:")
    print(f"入力: {test_text1}")
    print(f"出力: {result1}")
    print(f"<think>タグが保持されているか: {'<think>' in result1 and '</think>' in result1}")
    print()
    
    # テストケース2: HTMLエンティティを含む文字列
    test_text2 = """<think>ATPの生成について考えてみます。&lt;ATP&gt;は重要な分子です。</think>ATPはアデノシン三リン酸（adenosine triphosphate）で、細胞内でエネルギー貯蔵と転送の役割を果たします。"""
    
    result2 = _decode_xml_entities(test_text2)
    print("テストケース2:")
    print(f"入力: {test_text2}")
    print(f"出力: {result2}")
    print(f"<think>タグが保持されているか: {'<think>' in result2 and '</think>' in result2}")
    print(f"HTMLエンティティがデコードされているか: {'<ATP>' in result2}")
    print()
    
    # テストケース3: 複数の<think>タグ
    test_text3 = """<think>最初の思考プロセス</think>最初の回答<think>二番目の思考プロセス</think>追加の説明"""
    
    result3 = _decode_xml_entities(test_text3)
    print("テストケース3:")
    print(f"入力: {test_text3}")
    print(f"出力: {result3}")
    print(f"複数の<think>タグが保持されているか: {result3.count('<think>') == 2 and result3.count('</think>') == 2}")
    print()
    
    # テストケース4: <think>タグなし、HTMLエンティティのみ
    test_text4 = """これは&amp;普通の&lt;回答&gt;です。"""
    
    result4 = _decode_xml_entities(test_text4)
    print("テストケース4:")
    print(f"入力: {test_text4}")
    print(f"出力: {result4}")
    print(f"HTMLエンティティがデコードされているか: {'&' in result4 and '<回答>' in result4}")
    print()

if __name__ == "__main__":
    test_think_tag_preservation()
