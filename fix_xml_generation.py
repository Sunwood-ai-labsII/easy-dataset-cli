#!/usr/bin/env python3
"""Q&Aジェネレーターのシステムメッセージを修正するスクリプト"""

import sys
import os

def fix_system_messages():
    """qa_generator.pyのシステムメッセージを修正"""
    file_path = "c:/Prj/easy-dataset-cli/easy_dataset_cli/qa_generator.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 古いシステムメッセージを新しいものに置換
    old_message = '"あなたは、XML形式で厳密に出力する優秀なアシスタントです。XMLの特殊文字（&, <, >, \\", \'）は適切にエスケープし、改行は含めずに出力してください。"'
    new_message = '"あなたは、XML形式で厳密に出力する優秀なアシスタントです。通常のXMLの特殊文字（&, \\", \'）は適切にエスケープしてください。ただし、<Question>、<Answer>、<think>タグはそのまま使用してください。改行は含めずに出力してください。"'
    
    # 置換実行
    new_content = content.replace(old_message, new_message)
    
    # 思考フロー用のメッセージも統一
    thinking_old = '"あなたは、XML形式で出力する優秀なアシスタントです。<think>タグは特別なタグなのでエスケープしないでください。それ以外のXMLの特殊文字（&, <, >, \\", \'）は適切にエスケープし、改行は含めずに出力してください。"'
    new_content = new_content.replace(thinking_old, new_message)
    
    # ファイルに書き戻し
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"修正完了: {file_path}")
    print(f"置換回数 (通常): {content.count(old_message)}")
    print(f"置換回数 (思考): {content.count(thinking_old)}")

if __name__ == "__main__":
    fix_system_messages()
