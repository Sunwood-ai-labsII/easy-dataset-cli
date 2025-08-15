# easy_dataset_cli/alpaca_converter.py
"""アルパカデータセット形式への変換とHugging Faceアップロード機能"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional
from rich.console import Console
from huggingface_hub import HfApi, create_repo
from datasets import Dataset
import os

console = Console()

def xml_to_alpaca_format(xml_file_path: Path) -> List[Dict[str, str]]:
    """XMLファイルをアルパカ形式のデータに変換する"""
    alpaca_data = []
    
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        genre = root.get('genre', 'Unknown')
        
        for pair in root.findall('Pair'):
            audience_elem = pair.find('Audience')
            question_elem = pair.find('Question')
            answer_elem = pair.find('Answer')
            
            if all([audience_elem is not None, question_elem is not None, answer_elem is not None]):
                audience = audience_elem.text or ""
                question = question_elem.text or ""
                answer = answer_elem.text or ""
                # Answerタグの内容をそのままoutputに入れる（<think>...</think>含む）
                alpaca_entry = {
                    "instruction": question,
                    "input": "",  # アルパカ形式では通常空文字
                    "output": answer,
                    "genre": genre,
                    "audience": audience
                }
                alpaca_data.append(alpaca_entry)
                
    except ET.ParseError as e:
        console.print(f"[bold red]XMLファイルの解析エラー:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]予期しないエラー:[/bold red] {e}")
    
    return alpaca_data

def convert_all_xml_to_alpaca(qa_dir: Path, output_file: Path) -> List[Dict[str, str]]:
    """QAディレクトリ内のすべてのXMLファイルをアルパカ形式に変換"""
    all_alpaca_data = []
    
    xml_files = list(qa_dir.glob("*.xml"))
    
    if not xml_files:
        console.print(f"[yellow]XMLファイルが見つかりません: {qa_dir}[/yellow]")
        return all_alpaca_data
    
    console.print(f"[green]{len(xml_files)}個のXMLファイルを変換中...[/green]")
    
    for xml_file in xml_files:
        console.print(f"[dim]変換中: {xml_file.name}[/dim]")
        alpaca_data = xml_to_alpaca_format(xml_file)
        all_alpaca_data.extend(alpaca_data)
        console.print(f"[green]✓[/green] {len(alpaca_data)}個のエントリを追加")
    
    # JSONファイルに保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_alpaca_data, f, ensure_ascii=False, indent=2)
    
    console.print(f"[bold green]✓[/bold green] 合計{len(all_alpaca_data)}個のエントリを "
                  f"[cyan]{output_file}[/cyan] に保存しました")
    
    return all_alpaca_data

def upload_to_huggingface(
    dataset_data: List[Dict[str, str]],
    repo_name: str,
    hf_token: Optional[str] = None,
    private: bool = False,
    commit_message: str = "Upload alpaca dataset",
    readme_file: Optional[Path] = None
) -> bool:
    """Hugging Face Hubにデータセットをアップロード"""
    
    if not hf_token:
        hf_token = os.getenv("HUGGINGFACE_TOKEN")
        if not hf_token:
            console.print("[bold red]HUGGINGFACE_TOKENが設定されていません！[/bold red]")
            console.print("[yellow]環境変数またはコマンドライン引数でトークンを指定してください[/yellow]")
            return False
    
    try:
        # HfApiインスタンスを作成
        api = HfApi(token=hf_token)
        
        # リポジトリを作成（既に存在する場合はスキップ）
        try:
            create_repo(
                repo_id=repo_name,
                token=hf_token,
                repo_type="dataset",
                private=private,
                exist_ok=True
            )
            console.print(f"[green]✓[/green] リポジトリを作成/確認しました: [cyan]{repo_name}[/cyan]")
        except Exception as e:
            console.print(f"[yellow]リポジトリ作成時の警告: {e}[/yellow]")
        
        # データセットを作成
        dataset = Dataset.from_list(dataset_data)
        
        # Hugging Face Hubにプッシュ
        dataset.push_to_hub(
            repo_id=repo_name,
            token=hf_token,
            commit_message=commit_message,
            private=private
        )
        
        # README.mdが指定されている場合はアップロード
        if readme_file and readme_file.exists():
            try:
                api.upload_file(
                    path_or_fileobj=readme_file,
                    path_in_repo="README.md",
                    repo_id=repo_name,
                    repo_type="dataset",
                    commit_message=f"Update README.md",
                    token=hf_token
                )
                console.print(f"[green]✓[/green] README.mdをアップロードしました!")
            except Exception as readme_error:
                console.print(f"[yellow]README.mdアップロードの警告: {readme_error}[/yellow]")
        
        console.print(f"[bold green]✓[/bold green] データセットをアップロードしました!")
        console.print(f"[cyan]https://huggingface.co/datasets/{repo_name}[/cyan]")
        
        return True
        
    except Exception as e:
        console.print(f"[bold red]Hugging Faceアップロードエラー:[/bold red] {e}")
        return False

def create_dataset_card(
    dataset_data: List[Dict[str, str]], 
    output_file: Path,
    dataset_name: str = "Generated QA Dataset"
) -> None:
    """データセットカード（README.md）を生成"""
    
    # 統計情報を計算
    total_entries = len(dataset_data)
    genres = set(entry.get('genre', 'Unknown') for entry in dataset_data)
    audiences = set(entry.get('audience', 'Unknown') for entry in dataset_data)
    
    # データセットカードの内容
    card_content = f"""---
license: mit
task_categories:
- question-answering
- text-generation
language:
- ja
tags:
- alpaca
- qa
- japanese
size_categories:
- {get_size_category(total_entries)}
---

# {dataset_name}

このデータセットは、easy-dataset-cliを使用して生成されたアルパカ形式の日本語Q&Aデータセットです。

## データセット概要

- **総エントリ数**: {total_entries:,}
- **形式**: Alpaca形式
- **言語**: 日本語
- **ライセンス**: MIT

## データ構造

各エントリは以下の形式です：

```json
{{
  "instruction": "質問文",
  "input": "",
  "output": "回答文",
  "genre": "ジャンル",
  "audience": "対象読者"
}}
```

## ジャンル分布

含まれるジャンル:
{chr(10).join(f"- {genre}" for genre in sorted(genres))}

## 対象読者分布

含まれる対象読者:
{chr(10).join(f"- {audience}" for audience in sorted(audiences))}

## 使用方法

```python
from datasets import load_dataset

dataset = load_dataset("{dataset_name}")
```

## 生成ツール

このデータセットは[easy-dataset-cli](https://github.com/Sunwood-ai-labsII/easy-dataset-cli)を使用して生成されました。
"""
    
    output_file.write_text(card_content, encoding='utf-8')
    console.print(f"[green]✓[/green] データセットカードを生成しました: [cyan]{output_file}[/cyan]")

def get_size_category(count: int) -> str:
    """エントリ数に基づいてサイズカテゴリを返す"""
    if count < 1000:
        return "n<1K"
    elif count < 10000:
        return "1K<n<10K"
    elif count < 100000:
        return "10K<n<100K"
    elif count < 1000000:
        return "100K<n<1M"
    else:
        return "n>1M"
