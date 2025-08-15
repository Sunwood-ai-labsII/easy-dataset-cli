# easy_dataset_cli/main.py
"""CLIエントリーポイント"""

from pathlib import Path
from typing_extensions import Annotated
import typer
from rich.console import Console
from rich.progress import Progress
from dotenv import load_dotenv

from .core import (
    split_text,
    parse_ga_file,
    generate_qa_for_chunk_with_ga,
    generate_qa_for_chunk_with_ga_and_fulltext,
    convert_to_xml_by_genre,
    generate_ga_definitions,
    parse_ga_definitions_from_xml,
    save_ga_definitions_by_genre,
    create_output_directories,
    sanitize_filename,
    convert_all_xml_to_alpaca,
    upload_to_huggingface,
    create_dataset_card
)

# .envファイルを読み込む
load_dotenv()

app = typer.Typer(
    help="テキストファイルからQ&Aペアを生成するシンプルなCLIツール。",
    context_settings={"help_option_names": ["-h", "--help"]}
)
console = Console()


@app.command()
def create_ga(
    file_path: Annotated[Path, typer.Argument(
        exists=True, dir_okay=False, readable=True,
        help="GAペアの定義を生成するための元のテキストファイル。"
    )],
    output_dir: Annotated[Path, typer.Option(
        "--output-dir", "-o", file_okay=False, dir_okay=True, writable=True,
        help="生成されたGAペア定義ファイルを保存するディレクトリ。"
    )],
    model: Annotated[str, typer.Option(
        "--model", "-m",
        help="GAペア定義の生成に使用するLLMモデル名。"
    )] = "openrouter/openai/gpt-oss-120b",
    num_ga_pairs: Annotated[int, typer.Option(
        "--num-ga-pairs", "-g",
        help="生成するGAペアの数。指定しない場合はLLMが適切な数を決定します。"
    )] = 5,
):
    """元の文章を分析し、GAペア定義をXML形式で生成し、Genreごとにマークダウンファイルに保存します。"""
    console.print(f"ファイルを読み込んでいます: [cyan]{file_path}[/cyan]")

    try:
        text = file_path.read_text(encoding="utf-8")
        console.print(f"[dim]読み込んだテキスト長: {len(text)} 文字[/dim]")

        console.print("[bold green]LLMに最適なGAペアを提案させています...[/bold green]")
        xml_content = generate_ga_definitions(text, model=model, num_ga_pairs=num_ga_pairs)

        # 出力ディレクトリ構造を作成
        dirs = create_output_directories(output_dir)
        console.print(f"[dim]出力ディレクトリを作成しました: ga/, logs/, qa/[/dim]")
        
        # LLMのrawレスポンスをlogsディレクトリに保存
        raw_file_path = dirs["logs"] / "raw.md"
        raw_file_path.write_text(xml_content, encoding="utf-8")
        console.print(f"[green]✓[/green] LLMのrawレスポンスを保存しました: [cyan]{raw_file_path}[/cyan]")

        console.print("[bold green]XMLからGAペアを解析しています...[/bold green]")
        # XMLからGAペアを解析
        ga_pairs = parse_ga_definitions_from_xml(xml_content)
        
        if not ga_pairs:
            console.print("[bold red]有効なGAペアが生成されませんでした。[/bold red]")
            console.print("[yellow]生成されたXMLの内容を確認してください:[/yellow]")
            console.print(xml_content)
            raise typer.Exit(code=1)

        # 元のXMLファイルをgaディレクトリに保存（クリーンなXMLのみ）
        xml_file_path = dirs["ga"] / "ga_definitions.xml"
        # XMLタグ部分のみを抽出して保存
        xml_start = xml_content.find("<GADefinitions>")
        xml_end = xml_content.rfind("</GADefinitions>")
        if xml_start != -1 and xml_end != -1:
            clean_xml = xml_content[xml_start: xml_end + len("</GADefinitions>")]
            xml_file_path.write_text(clean_xml, encoding="utf-8")
            console.print(f"[green]✓[/green] GA定義XMLファイルを保存しました: [cyan]{xml_file_path}[/cyan]")

        # Genreごとにマークダウンファイルをgaディレクトリに保存
        save_ga_definitions_by_genre(ga_pairs, dirs["ga"])

        console.print(
            f"\n[bold green]✓[/bold green] {len(ga_pairs)}個のGAペアを "
            f"[cyan]{dirs['ga']}[/cyan] に保存しました。"
        )
        console.print(
            "[yellow]ヒント: 生成されたファイルをレビューし、必要に応じて編集してから "
            "`generate` コマンドで使用してください。[/yellow]"
        )

    except Exception as e:
        console.print(
            f"[bold red]GA定義ファイルの生成中にエラーが発生しました:[/bold red] {e}"
        )
        raise typer.Exit(code=1)


@app.command()
def generate(
    file_path: Annotated[Path, typer.Argument(
        exists=True, dir_okay=False, readable=True,
        help="元のテキストファイルへのパス。"
    )],
    ga_file: Annotated[Path, typer.Option(
        "--ga-file", "-g", exists=True, dir_okay=False, readable=True,
        help="Genre-Audienceペアを定義したXMLまたはMarkdownファイルへのパス。gaディレクトリのga_definitions.xmlを推奨。"
    )],
    output_dir: Annotated[Path, typer.Option(
        "--output-dir", "-o", file_okay=False, dir_okay=True, writable=True,
        help="生成されたXMLファイルを保存するディレクトリ。指定しない場合はコンソールに出力します。"
    )] = None,
    model: Annotated[str, typer.Option(
        "--model", "-m",
        help="Q&Aペアの生成に使用するLLMモデル名。"
    )] = "openrouter/openai/gpt-oss-120b",
    chunk_size: Annotated[int, typer.Option(
        help="テキストチャンクの最大サイズ。"
    )] = 2000,
    chunk_overlap: Annotated[int, typer.Option(
        help="チャンク間のオーバーラップサイズ。"
    )] = 200,
    num_qa_pairs: Annotated[int, typer.Option(
        "--num-qa-pairs", "-q",
        help="各チャンク・GAペアの組み合わせで生成するQ&Aペアの数。指定しない場合はLLMが適切な数を決定します。"
    )] = 10,
    use_fulltext: Annotated[bool, typer.Option(
        "--use-fulltext", "-f",
        help="全文をコンテキストとして含めてQA生成を行います。より文脈を理解したQAが生成されますが、処理時間とコストが増加します。"
    )] = False,
    append_mode: Annotated[bool, typer.Option(
        "--append", "-A",
        help="既存のXMLファイルに新しいQ&Aを追加します。指定しない場合は上書きします。"
    )] = False,
    export_alpaca: Annotated[bool, typer.Option(
        "--export-alpaca", "-a",
        help="生成されたQ&AペアをAlpaca形式のJSONファイルとして出力します。"
    )] = False,
    upload_hf: Annotated[bool, typer.Option(
        "--upload-hf", "-u",
        help="生成されたデータセットをHugging Face Hubにアップロードします。"
    )] = False,
    hf_repo_name: Annotated[str, typer.Option(
        "--hf-repo-name", "-r",
        help="Hugging Face Hubのリポジトリ名（例: username/dataset-name）"
    )] = "",
    hf_token: Annotated[str, typer.Option(
        "--hf-token", "-t",
        help="Hugging Face APIトークン（環境変数HUGGINGFACE_TOKENからも取得可能）"
    )] = "",
    hf_private: Annotated[bool, typer.Option(
        "--hf-private",
        help="Hugging Faceリポジトリをプライベートにします。"
    )] = False,
):
    """テキストファイルとGA定義からQ&Aペアを生成し、Genre別のXMLファイルとして出力します。
    
    --use-fulltextオプションを使用すると、各チャンクの処理時に全文をコンテキストとして含めることで、
    より文脈を理解した高品質なQ&Aペアを生成できます。ただし、処理時間とAPIコストが増加します。
    """
    try:
        console.print(f"ファイルを読み込んでいます: [cyan]{file_path}[/cyan]")
        text = file_path.read_text(encoding="utf-8")

        console.print(f"GAペアを解析しています: [cyan]{ga_file}[/cyan]")
        ga_pairs = parse_ga_file(ga_file)

        if not ga_pairs:
            console.print("[bold red]有効なGAペアが定義ファイルに見つかりませんでした。[/bold red]")
            raise typer.Exit(code=1)

        console.print(f"[green]{len(ga_pairs)}[/green] 個のGAペアを見つけました。")

        console.print("テキストをチャンクに分割しています...")
        chunks = split_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        console.print(f"[green]{len(chunks)}[/green] 個のチャンクを作成しました。")

        all_qa_pairs_with_ga = []
        total_tasks = len(chunks) * len(ga_pairs)
        
        # 出力ディレクトリがある場合は構造を作成
        dirs = None
        if output_dir:
            dirs = create_output_directories(output_dir)
            console.print(f"[dim]出力ディレクトリを作成しました: ga/, logs/, qa/[/dim]")

        # 全文使用の場合は警告を表示
        if use_fulltext:
            console.print("[yellow]⚠ 全文コンテキストモードが有効です。処理時間とコストが増加する可能性があります。[/yellow]")
            console.print(f"[dim]全文長: {len(text)} 文字[/dim]")

        with Progress(console=console) as progress:
            task = progress.add_task("[green]Q&Aペアを生成中...", total=total_tasks)

            for chunk in chunks:
                for ga_pair in ga_pairs:
                    if use_fulltext:
                        qa_pairs = generate_qa_for_chunk_with_ga_and_fulltext(
                            chunk=chunk,
                            full_text=text,
                            model=model,
                            ga_pair=ga_pair,
                            logs_dir=dirs["logs"] if dirs else None,
                            num_qa_pairs=num_qa_pairs
                        )
                    else:
                        qa_pairs = generate_qa_for_chunk_with_ga(
                            chunk, model=model, ga_pair=ga_pair,
                            logs_dir=dirs["logs"] if dirs else None,
                            num_qa_pairs=num_qa_pairs
                        )

                    for pair in qa_pairs:
                        all_qa_pairs_with_ga.append({
                            "genre": ga_pair['genre']['title'],
                            "audience": ga_pair['audience']['title'],
                            "question": pair['question'],
                            "answer": pair['answer'],
                        })

                    progress.update(
                        task, advance=1,
                        description=f"Genre: {ga_pair['genre']['title']}"
                    )

        console.print(
            f"\n合計 [bold green]{len(all_qa_pairs_with_ga)}[/bold green] "
            "個のQ&Aペアを生成しました。"
        )

        xml_outputs_by_genre = convert_to_xml_by_genre(all_qa_pairs_with_ga, dirs["qa"] if dirs else None, append_mode)

        if dirs:
            console.print(f"XMLファイルを [cyan]{dirs['qa']}[/cyan] に保存しています...")

            for genre, xml_content in xml_outputs_by_genre.items():
                safe_genre_name = sanitize_filename(genre)
                output_file_path = dirs["qa"] / f"{safe_genre_name}.xml"
                output_file_path.write_text(xml_content, encoding="utf-8")
                console.print(f"  - [green]✓[/green] {output_file_path.name}")

            console.print("\n[bold green]すべてのファイルの保存が完了しました。[/bold green]")
            
            # アルパカ形式でのエクスポート
            if export_alpaca:
                console.print("\n[bold blue]Alpaca形式のJSONファイルを生成中...[/bold blue]")
                alpaca_file = dirs["base"] / "dataset_alpaca.json"
                alpaca_data = convert_all_xml_to_alpaca(dirs["qa"], alpaca_file)
                
                # データセットカードを生成
                readme_file = dirs["base"] / "README.md"
                create_dataset_card(alpaca_data, readme_file, "Generated QA Dataset")
                
                # Hugging Face Hubにアップロード
                if upload_hf:
                    if not hf_repo_name:
                        console.print("[bold red]--hf-repo-nameが指定されていません！[/bold red]")
                        console.print("[yellow]例: --hf-repo-name username/my-qa-dataset[/yellow]")
                    else:
                        console.print(f"\n[bold blue]Hugging Face Hubにアップロード中...[/bold blue]")
                        success = upload_to_huggingface(
                            dataset_data=alpaca_data,
                            repo_name=hf_repo_name,
                            hf_token=hf_token if hf_token else None,
                            private=hf_private,
                            commit_message=f"Upload QA dataset with {len(alpaca_data)} entries",
                            readme_file=readme_file
                        )
                        if not success:
                            console.print("[bold red]Hugging Faceアップロードに失敗しました[/bold red]")
        else:
            console.print("\n--- 生成されたQ&Aペア (Genre別XML) ---")
            for genre, xml_content in xml_outputs_by_genre.items():
                console.print(f"\n[bold yellow]## Genre: {genre} ##[/bold yellow]")
                console.print(xml_content, overflow="fold")
    
    except Exception as e:
        console.print(f"[bold red]エラーが発生しました:[/bold red]")
        console.print(f"[bold red]エラータイプ:[/bold red] {type(e).__name__}")
        console.print(f"[bold red]エラーメッセージ:[/bold red] {str(e)}")
        console.print(f"[bold red]トレースバック:[/bold red]")
        import traceback
        console.print(traceback.format_exc())
        raise typer.Exit(code=1)


@app.command()
def convert_to_alpaca(
    qa_dir: Annotated[Path, typer.Argument(
        exists=True, dir_okay=True, readable=True,
        help="XMLファイルが保存されているqaディレクトリへのパス。"
    )],
    output_file: Annotated[Path, typer.Option(
        "--output-file", "-o", file_okay=True, dir_okay=False,
        help="出力するAlpaca形式JSONファイルのパス。"
    )] = None,
    upload_hf: Annotated[bool, typer.Option(
        "--upload-hf", "-u",
        help="生成されたデータセットをHugging Face Hubにアップロードします。"
    )] = False,
    hf_repo_name: Annotated[str, typer.Option(
        "--hf-repo-name", "-r",
        help="Hugging Face Hubのリポジトリ名（例: username/dataset-name）"
    )] = "",
    hf_token: Annotated[str, typer.Option(
        "--hf-token", "-t",
        help="Hugging Face APIトークン（環境変数HUGGINGFACE_TOKENからも取得可能）"
    )] = "",
    hf_private: Annotated[bool, typer.Option(
        "--hf-private",
        help="Hugging Faceリポジトリをプライベートにします。"
    )] = False,
):
    """既存のXMLファイルをAlpaca形式のJSONに変換し、オプションでHugging Face Hubにアップロードします。"""
    
    try:
        # デフォルトの出力ファイル名を設定
        if output_file is None:
            output_file = qa_dir.parent / "dataset_alpaca.json"
        
        console.print(f"XMLファイルを変換中: [cyan]{qa_dir}[/cyan]")
        
        # アルパカ形式に変換
        alpaca_data = convert_all_xml_to_alpaca(qa_dir, output_file)
        
        if not alpaca_data:
            console.print("[bold red]変換できるデータが見つかりませんでした。[/bold red]")
            raise typer.Exit(code=1)
        
        # データセットカードを生成
        readme_file = output_file.parent / "README.md"
        create_dataset_card(alpaca_data, readme_file, "Converted QA Dataset")
        
        # Hugging Face Hubにアップロード
        if upload_hf:
            if not hf_repo_name:
                console.print("[bold red]--hf-repo-nameが指定されていません！[/bold red]")
                console.print("[yellow]例: --hf-repo-name username/my-qa-dataset[/yellow]")
                raise typer.Exit(code=1)
            
            console.print(f"\n[bold blue]Hugging Face Hubにアップロード中...[/bold blue]")
            success = upload_to_huggingface(
                dataset_data=alpaca_data,
                repo_name=hf_repo_name,
                hf_token=hf_token if hf_token else None,
                private=hf_private,
                commit_message=f"Upload converted QA dataset with {len(alpaca_data)} entries",
                readme_file=readme_file
            )
            
            if not success:
                console.print("[bold red]Hugging Faceアップロードに失敗しました[/bold red]")
                raise typer.Exit(code=1)
        
        console.print(f"\n[bold green]✓[/bold green] 変換が完了しました！")
        
    except Exception as e:
        console.print(f"[bold red]変換中にエラーが発生しました:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def aggregate_logs(
    output_dir: Annotated[Path, typer.Argument(
        exists=True, dir_okay=True, readable=True,
        help="logsフォルダが含まれる出力ディレクトリへのパス。"
    )]
):
    """logsフォルダ内のタイムスタンプ付きXMLファイルを集約してqaフォルダのXMLを生成します。"""
    
    try:
        logs_dir = output_dir / "logs"
        qa_dir = output_dir / "qa"
        
        if not logs_dir.exists():
            console.print(f"[bold red]logsフォルダが見つかりません: {logs_dir}[/bold red]")
            raise typer.Exit(code=1)
        
        console.print(f"logsフォルダ: [cyan]{logs_dir}[/cyan]")
        console.print(f"出力先qaフォルダ: [cyan]{qa_dir}[/cyan]")
        
        # XMLファイルを集約してqaフォルダに生成
        from easy_dataset_cli.core import aggregate_logs_xml_to_qa
        aggregate_logs_xml_to_qa(logs_dir, qa_dir)
        
        console.print(f"\n[bold green]✓[/bold green] 集約が完了しました！")
        
    except Exception as e:
        console.print(f"[bold red]エラーが発生しました:[/bold red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
