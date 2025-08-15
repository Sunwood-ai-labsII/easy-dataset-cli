#!/usr/bin/env python3
"""logsフォルダのXML集約機能のテストスクリプト"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), 'easy_dataset_cli'))

from easy_dataset_cli.xml_utils import aggregate_logs_xml_to_qa, load_existing_xml_file
from easy_dataset_cli.core import aggregate_logs_xml_to_qa as core_aggregate_logs_xml_to_qa
from rich.console import Console

console = Console()

def create_test_xml_files(logs_dir: Path):
    """テスト用のXMLファイルを作成"""
    
    # logsディレクトリを作成
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # テスト用XMLファイル1: FAQ_初心者ゲーマー
    faq_xml_content = '''<?xml version="1.0" ?>
<QAPairs genre="FAQ">
  <Pair>
    <Audience>初心者ゲーマー</Audience>
    <Question>東方Projectとは何ですか？</Question>
    <Answer>東方Projectは、上海アリス幻樂団によって制作された弾幕系シューティングゲームシリーズです。</Answer>
  </Pair>
  <Pair>
    <Audience>初心者ゲーマー</Audience>
    <Question>最初にどのゲームをプレイすればいいですか？</Question>
    <Answer>初心者には「東方紅魔郷」や「東方妖々夢」がおすすめです。</Answer>
  </Pair>
</QAPairs>'''
    
    faq_file = logs_dir / "qa_pairs_FAQ_初心者ゲーマー_20250815_171008.xml"
    faq_file.write_text(faq_xml_content, encoding='utf-8')
    
    # テスト用XMLファイル2: テクニカルガイド_PCゲーミング愛好者
    tech_xml_content = '''<?xml version="1.0" ?>
<QAPairs genre="テクニカルガイド">
  <Pair>
    <Audience>PCゲーミング愛好者</Audience>
    <Question>東方Projectのシステム要件は？</Question>
    <Answer>東方Projectのゲームは比較的古いPCでも動作するように設計されています。</Answer>
  </Pair>
  <Pair>
    <Audience>PCゲーミング愛好者</Audience>
    <Question>Steam版とダウンロード版の違いは？</Question>
    <Answer>Steam版は自動アップデート機能があり、クラウドセーブに対応しています。</Answer>
  </Pair>
</QAPairs>'''
    
    tech_file = logs_dir / "qa_pairs_テクニカルガイド_PCゲーミング愛好者_20250815_171009.xml"
    tech_file.write_text(tech_xml_content, encoding='utf-8')
    
    # テスト用XMLファイル3: FAQ_上級者
    faq_advanced_xml_content = '''<?xml version="1.0" ?>
<QAPairs genre="FAQ">
  <Pair>
    <Audience>上級者</Audience>
    <Question>東方Projectのキャラクター設定はどこで確認できますか？</Question>
    <Answer>公式サイトや各ゲームのマニュアル、二次創作情報サイトで詳細な設定を確認できます。</Answer>
  </Pair>
  <Pair>
    <Audience>上級者</Audience>
    <Question>弾幕の難易度設定について教えてください。</Question>
    <Answer>各ゲームには複数の難易度設定があり、特に「Extra」や'Phantasm'は非常に高い難易度です。</Answer>
  </Pair>
</QAPairs>'''
    
    faq_advanced_file = logs_dir / "qa_pairs_FAQ_上級者_20250815_171010.xml"
    faq_advanced_file.write_text(faq_advanced_xml_content, encoding='utf-8')

def test_aggregate_logs():
    """logsフォルダのXML集約機能のテスト"""
    
    print("=== logsフォルダのXML集約機能テスト ===\n")
    
    # 一時ディレクトリを作成
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        logs_dir = temp_path / "logs"
        qa_dir = temp_path / "qa"
        
        # テスト用XMLファイルを作成
        create_test_xml_files(logs_dir)
        
        console.print(f"テスト用logsディレクトリ: {logs_dir}")
        console.print(f"テスト用qaディレクトリ: {qa_dir}")
        
        # XMLファイルを集約
        console.print("\n[bold blue]XMLファイルを集約中...[/bold blue]")
        aggregate_logs_xml_to_qa(logs_dir, qa_dir)
        
        # 結果を確認
        console.print("\n[bold green]=== 集約結果 ===[/bold green]")
        
        # qaディレクトリ内のファイルを確認
        xml_files = list(qa_dir.glob("*.xml"))
        console.print(f"生成されたXMLファイル数: {len(xml_files)}")
        
        for xml_file in xml_files:
            console.print(f"\n[cyan]{xml_file.name}[/cyan]:")
            
            # XMLファイルの内容を確認
            qa_pairs = load_existing_xml_file(xml_file)
            console.print(f"  Q&Aペア数: {len(qa_pairs)}")
            
            for i, qa in enumerate(qa_pairs, 1):
                console.print(f"  {i}. [yellow]質問:[/yellow] {qa['question']}")
                console.print(f"     [yellow]回答:[/yellow] {qa['answer']}")
                console.print(f"     [dim]ジャンル:[/dim] {qa['genre']}")
                console.print(f"     [dim]対象読者:[/dim] {qa['audience']}")
        
        # 期待される結果を確認
        expected_files = ["FAQ.xml", "テクニカルガイド.xml"]
        console.print(f"\n[bold blue]=== 期待されるファイル ===[/bold blue]")
        for expected_file in expected_files:
            expected_path = qa_dir / expected_file
            if expected_path.exists():
                console.print(f"[green]✓[/green] {expected_file} が生成されました")
            else:
                console.print(f"[red]✗[/red] {expected_file} が生成されていません")
        
        # FAQ.xmlの内容を詳細に確認
        faq_file = qa_dir / "FAQ.xml"
        if faq_file.exists():
            console.print(f"\n[bold blue]=== FAQ.xmlの詳細確認 ===[/bold blue]")
            faq_content = faq_file.read_text(encoding='utf-8')
            console.print(faq_content)
        
        # テスト結果を返す
        success = len(xml_files) == 2 and all((qa_dir / f).exists() for f in expected_files)
        return success

if __name__ == "__main__":
    success = test_aggregate_logs()
    if success:
        console.print("\n✅ すべてのテストが成功しました！")
    else:
        console.print("\n❌ テストに失敗しました。")
    sys.exit(0 if success else 1)
