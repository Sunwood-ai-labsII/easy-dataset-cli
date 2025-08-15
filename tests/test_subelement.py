#!/usr/bin/env python3
"""サブエレメントでthinkタグを扱うテスト"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from easy_dataset_cli.qa_generator import _parse_answer_with_think, _save_qa_pairs_to_xml
from pathlib import Path

def test_parse_answer_with_think():
    """_parse_answer_with_think関数のテスト"""
    
    # テストケース1: <think>タグあり
    answer1 = "<think>これは思考プロセスです</think>これはテスト回答1です。"
    result1 = _parse_answer_with_think(answer1)
    print("テストケース1:", result1)
    
    # テストケース2: <think>タグなし
    answer2 = "これは普通の回答です。"
    result2 = _parse_answer_with_think(answer2)
    print("テストケース2:", result2)
    
    # テストケース3: 実際のQ&Aペア保存テスト
    qa_pairs = [
        {
            "question": "テスト質問1",
            "answer": "<think>これは思考プロセスです</think>これはテスト回答1です。"
        },
        {
            "question": "テスト質問2", 
            "answer": "これは普通の回答です。"
        }
    ]
    
    test_dir = Path("test_output")
    test_dir.mkdir(exist_ok=True)
    
    _save_qa_pairs_to_xml(qa_pairs, test_dir, "test_subelement.xml")
    
    # 生成されたファイルを読んで確認
    generated_file = test_dir / "test_subelement.xml"
    if generated_file.exists():
        content = generated_file.read_text(encoding='utf-8')
        print("\n生成されたXML:")
        print(content)
        
        if "&lt;think&gt;" in content:
            print("❌ <think>タグがエスケープされています!")
        else:
            print("✅ <think>タグはエスケープされていません!")
    
    # クリーンアップ
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)

if __name__ == "__main__":
    test_parse_answer_with_think()
