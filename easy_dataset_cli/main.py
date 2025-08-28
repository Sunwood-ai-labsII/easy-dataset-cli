# easy_dataset_cli/main.py
"""CLIエントリーポイント"""

from pathlib import Path
from typing_extensions import Annotated
import typer
from rich.console import Console
from rich.progress import Progress
from rich.text import Text
from rich.panel import Panel
from rich.columns import Columns
from rich.table import Table
from dotenv import load_dotenv
try:
    from art import tprint, text2art
    ART_AVAILABLE = True
except ImportError:
    ART_AVAILABLE = False

from .core import (
    split_text,
    parse_ga_file,
    generate_qa_for_chunk_with_ga,
    generate_qa_for_chunk_with_ga_and_fulltext,
    generate_qa_for_chunk_with_ga_and_thinking,
    convert_to_xml_by_genre,
    generate_ga_definitions,
    parse_ga_definitions_from_xml,
    save_ga_definitions_by_genre,
    create_output_directories,
    sanitize_filename,
    convert_all_xml_to_alpaca,
    upload_to_huggingface,
    create_dataset_card,
    find_text_files
)

# .envファイルを読み込む
load_dotenv()

app = typer.Typer(
    help="テキストファイルからQ&Aペアを生成するおしゃれなCLIツール。",
    context_settings={"help_option_names": ["-h", "--help"]}
)
console = Console()

def print_logo():
    """おしゃれなロゴを表示"""
    if ART_AVAILABLE:
        console.print("\n")
        # シンプルで読みやすいフォントを使用
        try:
            logo_text = text2art("Easy Dataset CLI", font="colossal")
        except:
            # フォールバックとして標準フォント
            logo_text = text2art("Easy Dataset CLI")
        
        # 各行を中央揃えに調整
        lines = logo_text.strip().split('\n')
        max_width = max(len(line.rstrip()) for line in lines) if lines else 0
        
        # パネル内で中央揃えするため、Textオブジェクトを使用
        logo_panel = Panel(
            Text(logo_text.strip(), style="bold cyan", justify="center"),
            title="[bold green]🚀 Easy Dataset CLI[/bold green]",
            subtitle="[italic]Powered by AI[/italic]",
            border_style="bright_blue",
            padding=(1, 2),
            expand=True  # 横幅一杯に展開
        )
        console.print(logo_panel)
    else:
        header = Panel(
            Text("🚀 Easy Dataset CLI\nテキストからQ&Aペアを自動生成", style="bold cyan", justify="center"),
            border_style="bright_blue",
            padding=(1, 2),
            expand=True  # 横幅一杯に展開
        )
        console.print(header)

def print_success_summary(message: str, details: list = None):
    """成功メッセージを美しく表示"""
    panel = Panel(
        f"[bold green]✨ {message}[/bold green]",
        border_style="green",
        padding=(1, 2)
    )
    console.print(panel)
    
    if details:
        table = Table(show_header=False, box=None)
        table.add_column("Item", style="cyan")
        for detail in details:
            table.add_row(f"  • {detail}")
        console.print(table)

def print_error_panel(error_msg: str):
    """エラーメッセージを美しく表示"""
    panel = Panel(
        f"[bold red]❌ エラー[/bold red]\n{error_msg}",
        border_style="red",
        padding=(1, 2)
    )
    console.print(panel)


@app.command()
def create_ga(
    file_path: Annotated[Path, typer.Argument(
        exists=True, readable=True,
        help="GAペアの定義を生成するための元のテキストファイルまたはフォルダ。フォルダを指定した場合、内部のテキストファイルをバッチ処理します。"
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
    print_logo()
    
    try:
        # フォルダかファイルかを判定
        if file_path.is_dir():
            # フォルダの場合：バッチ処理
            console.print(f"[bold blue]📁 フォルダ処理モード: {file_path}[/bold blue]")
            text_files = find_text_files(file_path)
            
            if not text_files:
                print_error_panel(f"指定されたフォルダにテキストファイルが見つかりませんでした: {file_path}")
                raise typer.Exit(code=1)
            
            console.print(f"[green]✓[/green] {len(text_files)}個のテキストファイルを発見しました")
            
            # バッチ処理用の設定テーブル
            batch_info_table = Table(show_header=False, box=None)
            batch_info_table.add_column("Key", style="bold cyan")
            batch_info_table.add_column("Value", style="white")
            batch_info_table.add_row("📁 入力フォルダ", str(file_path))
            batch_info_table.add_row("📄 ファイル数", str(len(text_files)))
            batch_info_table.add_row("📁 出力ディレクトリ", str(output_dir))
            batch_info_table.add_row("🤖 モデル", model)
            batch_info_table.add_row("🔢 GAペア数", str(num_ga_pairs))
            
            console.print(Panel(batch_info_table, title="[bold blue]🚀 バッチGAペア生成設定[/bold blue]", border_style="blue"))
            
            # ファイル一覧を表示
            files_table = Table(show_header=False, box=None)
            files_table.add_column("ファイル", style="cyan")
            for text_file in text_files[:10]:  # 最初の10個のみ表示
                files_table.add_row(f"• {text_file.name}")
            if len(text_files) > 10:
                files_table.add_row(f"... and {len(text_files) - 10} more files")
            
            console.print(Panel(files_table, title="[bold green]📄 処理予定ファイル[/bold green]", border_style="green"))
            
            return _batch_create_ga_files(text_files, output_dir, model, num_ga_pairs)
        else:
            # 単一ファイルの場合：既存の処理
            info_table = Table(show_header=False, box=None)
            info_table.add_column("Key", style="bold cyan")
            info_table.add_column("Value", style="white")
            info_table.add_row("📄 入力ファイル", str(file_path))
            info_table.add_row("📁 出力ディレクトリ", str(output_dir))
            info_table.add_row("🤖 モデル", model)
            info_table.add_row("🔢 GAペア数", str(num_ga_pairs))
            
            console.print(Panel(info_table, title="[bold blue]🚀 GAペア生成設定[/bold blue]", border_style="blue"))
            
            text = file_path.read_text(encoding="utf-8")
            console.print(f"[dim]✓ テキスト長: {len(text):,} 文字を読み込みました[/dim]\n")

        with console.status("[bold green]🤖 LLMにGAペアの提案を依頼中...[/bold green]"):
            xml_content = generate_ga_definitions(text, model=model, num_ga_pairs=num_ga_pairs)

        # 出力ディレクトリ構造を作成
        dirs = create_output_directories(output_dir)
        console.print(f"\n[dim]✓ 出力ディレクトリを作成: ga/, logs/, qa/[/dim]")
        
        # LLMのrawレスポンスをlogsディレクトリに保存
        raw_file_path = dirs["logs"] / "raw.md"
        raw_file_path.write_text(xml_content, encoding="utf-8")
        console.print(f"[green]✓[/green] LLMのrawレスポンスを保存: [cyan]{raw_file_path.name}[/cyan]")

        with console.status("[bold green]🔍 XMLからGAペアを解析中...[/bold green]"):
            # XMLからGAペアを解析
            ga_pairs = parse_ga_definitions_from_xml(xml_content)
        
        if not ga_pairs:
            print_error_panel("有効なGAペアが生成されませんでした。\n生成されたXMLの内容を確認してください。")
            console.print(Panel(xml_content, title="生成されたXML", border_style="yellow"))
            raise typer.Exit(code=1)

        # 元のXMLファイルをgaディレクトリに保存（クリーンなXMLのみ）
        xml_file_path = dirs["ga"] / "ga_definitions.xml"
        # XMLタグ部分のみを抽出して保存
        xml_start = xml_content.find("<GADefinitions>")
        xml_end = xml_content.rfind("</GADefinitions>")
        if xml_start != -1 and xml_end != -1:
            clean_xml = xml_content[xml_start: xml_end + len("</GADefinitions>")]
            xml_file_path.write_text(clean_xml, encoding="utf-8")
            console.print(f"[green]✓[/green] GA定義XMLファイルを保存: [cyan]{xml_file_path.name}[/cyan]")

        # Genreごとにマークダウンファイルをgaディレクトリに保存
        save_ga_definitions_by_genre(ga_pairs, dirs["ga"])

        # 成功メッセージを美しく表示
        details = [
            f"{len(ga_pairs)}個のGAペアを生成",
            f"保存先: {dirs['ga']}",
            "XMLファイルとマークダウンファイルを作成"
        ]
        print_success_summary("GAペアの生成が完了しました！", details)
        
        next_steps_panel = Panel(
            "🔍 生成されたファイルをレビュー\n"
            "✏️ 必要に応じて編集\n"
            "🚀 `generate` コマンドでQ&A生成へ",
            title="[bold yellow]🔄 次のステップ[/bold yellow]",
            border_style="yellow"
        )
        console.print(next_steps_panel)

    except Exception as e:
        print_error_panel(f"GA定義ファイルの生成中にエラーが発生しました:\n{e}")
        raise typer.Exit(code=1)


@app.command()
def generate(
    file_path: Annotated[Path, typer.Argument(
        exists=True, readable=True,
        help="元のテキストファイルまたはフォルダへのパス。フォルダを指定した場合、内部のテキストファイルをバッチ処理します。"
    )],
    ga_file: Annotated[Path, typer.Option(
        "--ga-file", "-g", exists=True, dir_okay=False, readable=True,
        help="Genre-Audienceペアを定義したXMLまたはMarkdownファイルへのパス。バッチ処理で全ファイルに共通の定義を適用する場合に使用します。"
    )] = None,
    ga_base_dir: Annotated[Path, typer.Option(
        "--ga-base-dir", "-gb", exists=True, file_okay=False, dir_okay=True, readable=True,
        help="GA定義フォルダの親ディレクトリ。バッチ処理時に各入力ファイルに対応するGA定義を自動検出する場合に使用します。"
    )] = None,
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
    use_thinking: Annotated[bool, typer.Option(
        "--use-thinking", "-T",
        help="各Q&Aペアに思考プロセスを追加して生成します。より深い理解と説明が可能になりますが、処理時間とコストが増加します。"
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
    print_logo()
    
    try:
        # フォルダかファイルかを判定
        if file_path.is_dir():
            # フォルダの場合：バッチ処理
            console.print(f"[bold blue]📁 フォルダ処理モード: {file_path}[/bold blue]")
            text_files = find_text_files(file_path)
            
            if not text_files:
                print_error_panel(f"指定されたフォルダにテキストファイルが見つかりませんでした: {file_path}")
                raise typer.Exit(code=1)
            
            console.print(f"[green]✓[/green] {len(text_files)}個のテキストファイルを発見しました")
            
            # バッチ処理用の設定テーブル
            batch_settings_table = Table(show_header=False, box=None)
            batch_settings_table.add_column("項目", style="bold cyan")
            batch_settings_table.add_column("値", style="white")
            batch_settings_table.add_row("📁 入力フォルダ", str(file_path))
            batch_settings_table.add_row("📄 ファイル数", str(len(text_files)))
            
            # GA定義の表示
            if ga_file:
                batch_settings_table.add_row("📊 GA定義", str(ga_file))
            elif ga_base_dir:
                batch_settings_table.add_row("📊 GA定義ベースディレクトリ", str(ga_base_dir))
            else:
                batch_settings_table.add_row("📊 GA定義", "未指定")
            
            batch_settings_table.add_row("� 出力先", str(output_dir) if output_dir else "コンソール")
            batch_settings_table.add_row("🤖 モデル", model)
            batch_settings_table.add_row("🔢 Q&A数/チャンク", str(num_qa_pairs))
            
            mode_options = []
            if use_fulltext: mode_options.append("📋 全文コンテキスト")
            if use_thinking: mode_options.append("🤔 思考フロー")
            if append_mode: mode_options.append("➕ 追加モード")
            if export_alpaca: mode_options.append("🤙 Alpaca形式")
            if upload_hf: mode_options.append("🤗 HFアップロード")
            
            if mode_options:
                batch_settings_table.add_row("⚙️ オプション", ", ".join(mode_options))
            
            console.print(Panel(batch_settings_table, title="[bold blue]🚀 バッチQ&A生成設定[/bold blue]", border_style="blue"))
            
            # ファイル一覧を表示
            files_table = Table(show_header=False, box=None)
            files_table.add_column("ファイル", style="cyan")
            for text_file in text_files[:10]:  # 最初の10個のみ表示
                files_table.add_row(f"• {text_file.name}")
            if len(text_files) > 10:
                files_table.add_row(f"... and {len(text_files) - 10} more files")
            
            console.print(Panel(files_table, title="[bold green]📄 処理予定ファイル[/bold green]", border_style="green"))
            
            # バッチ処理のバリデーション
            if not ga_file and not ga_base_dir:
                print_error_panel("バッチ処理を行うには、--ga-file または --ga-base-dir のいずれかを指定する必要があります。")
                raise typer.Exit(code=1)
            
            if ga_file and ga_base_dir:
                print_error_panel("--ga-file と --ga-base-dir は同時に使用できません。")
                raise typer.Exit(code=1)
            
            # 各ファイルをバッチ処理
            return _batch_process_files(text_files, ga_file, ga_base_dir, output_dir, model, chunk_size, chunk_overlap,
                                      num_qa_pairs, use_fulltext, use_thinking, append_mode,
                                      export_alpaca, upload_hf, hf_repo_name, hf_token, hf_private)
        else:
            # 単一ファイルの場合：既存の処理
            # 設定情報をテーブルで表示
            settings_table = Table(show_header=False, box=None)
            settings_table.add_column("項目", style="bold cyan")
            settings_table.add_column("値", style="white")
            settings_table.add_row("📄 入力ファイル", str(file_path))
            settings_table.add_row("📊 GA定義", str(ga_file) if ga_file else "未指定")
            settings_table.add_row("📁 出力先", str(output_dir) if output_dir else "コンソール")
            settings_table.add_row("🤖 モデル", model)
            settings_table.add_row("🔢 Q&A数/チャンク", str(num_qa_pairs))
            
            mode_options = []
            if use_fulltext: mode_options.append("📋 全文コンテキスト")
            if use_thinking: mode_options.append("🤔 思考フロー")
            if append_mode: mode_options.append("➕ 追加モード")
            if export_alpaca: mode_options.append("🤙 Alpaca形式")
            if upload_hf: mode_options.append("🤗 HFアップロード")
            
            if mode_options:
                settings_table.add_row("⚙️ オプション", ", ".join(mode_options))
            
            console.print(Panel(settings_table, title="[bold blue]🚀 Q&A生成設定[/bold blue]", border_style="blue"))
            
            # 単一ファイル処理のバリデーション
            if not ga_file:
                print_error_panel("単一ファイル処理には --ga-file の指定が必須です。")
                raise typer.Exit(code=1)
            
            text = file_path.read_text(encoding="utf-8")
            console.print(f"\n[dim]✓ テキスト長: {len(text):,} 文字を読み込みました[/dim]")

        with console.status("🔍 GAペアを解析中..."):
            ga_pairs = parse_ga_file(ga_file)

        if not ga_pairs:
            print_error_panel("有効なGAペアが定義ファイルに見つかりませんでした。")
            raise typer.Exit(code=1)

        console.print(f"\n[green]✓[/green] {len(ga_pairs)}個のGAペアを発見しました")

        with console.status("✂️ テキストをチャンクに分割中..."):
            chunks = split_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        console.print(f"[green]✓[/green] {len(chunks)}個のチャンクを作成しました")

        all_qa_pairs_with_ga = []
        total_tasks = len(chunks) * len(ga_pairs)
        
        # 出力ディレクトリがある場合は構造を作成
        dirs = None
        if output_dir:
            dirs = create_output_directories(output_dir)
            console.print(f"[dim]✓ 出力ディレクトリを作成: ga/, logs/, qa/[/dim]")

        # モード警告を表示
        warnings = []
        if use_fulltext:
            warnings.append(f"📋 全文コンテキストモード ({len(text):,} 文字)")
        if use_thinking:
            warnings.append("🤔 思考フローモード")
        
        if warnings:
            warning_panel = Panel(
                "\n".join(warnings) + "\n\n⚠️ 処理時間とAPIコストが増加する可能性があります",
                title="[bold yellow]⚠️ モード警告[/bold yellow]",
                border_style="yellow"
            )
            console.print(warning_panel)

        with Progress(console=console) as progress:
            task = progress.add_task("[green]Q&Aペアを生成中...", total=total_tasks)

            for chunk in chunks:
                for ga_pair in ga_pairs:
                    if use_thinking:
                        qa_pairs = generate_qa_for_chunk_with_ga_and_thinking(
                            chunk=chunk,
                            full_text=text if use_fulltext else "",
                            model=model,
                            ga_pair=ga_pair,
                            logs_dir=dirs["logs"] if dirs else None,
                            num_qa_pairs=num_qa_pairs
                        )
                    elif use_fulltext:
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
                        qa_entry = {
                            "genre": ga_pair['genre']['title'],
                            "audience": ga_pair['audience']['title'],
                            "question": pair['question'],
                            "answer": pair['answer'],  # <think>...</think>回答...形式がそのまま入る
                        }
                        all_qa_pairs_with_ga.append(qa_entry)

                    progress.update(
                        task, advance=1,
                        description=f"Genre: {ga_pair['genre']['title']}"
                    )

        generation_summary = Panel(
            f"✨ [bold green]{len(all_qa_pairs_with_ga)}[/bold green] 個のQ&Aペアを生成完了！",
            title="[bold green]✅ 生成結果[/bold green]",
            border_style="green"
        )
        console.print(generation_summary)

        xml_outputs_by_genre = convert_to_xml_by_genre(all_qa_pairs_with_ga, dirs["qa"] if dirs else None, append_mode)

        if dirs:
            with console.status(f"💾 XMLファイルを {dirs['qa']} に保存中..."):
                saved_files = []
                for genre, xml_content in xml_outputs_by_genre.items():
                    safe_genre_name = sanitize_filename(genre)
                    output_file_path = dirs["qa"] / f"{safe_genre_name}.xml"
                    output_file_path.write_text(xml_content, encoding="utf-8")
                    saved_files.append(output_file_path.name)
            
            files_table = Table(show_header=False, box=None)
            files_table.add_column("ファイル", style="cyan")
            for file_name in saved_files:
                files_table.add_row(f"✓ {file_name}")
            
                console.print(Panel(files_table, title="[bold green]💾 保存済みファイル[/bold green]", border_style="green"))
            
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
        import traceback
        error_details = f"エラータイプ: {type(e).__name__}\nメッセージ: {str(e)}\n\nトレースバック:\n{traceback.format_exc()}"
        print_error_panel(error_details)
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
    
    print_logo()
    
    conversion_table = Table(show_header=False, box=None)
    conversion_table.add_column("項目", style="bold cyan")
    conversion_table.add_column("値", style="white")
    conversion_table.add_row("📁 入力ディレクトリ", str(qa_dir))
    conversion_table.add_row("💾 出力ファイル", str(output_file) if output_file else "自動")
    if upload_hf:
        conversion_table.add_row("🤗 HFリポジトリ", hf_repo_name or "未指定")
    
    console.print(Panel(conversion_table, title="[bold blue]🔄 Alpaca形式変換[/bold blue]", border_style="blue"))
    
    try:
        # デフォルトの出力ファイル名を設定
        if output_file is None:
            output_file = qa_dir.parent / "dataset_alpaca.json"
        
        with console.status(f"🔄 XMLファイルをAlpaca形式に変換中..."):
            alpaca_data = convert_all_xml_to_alpaca(qa_dir, output_file)
        
        if not alpaca_data:
            print_error_panel("変換できるデータが見つかりませんでした。")
            raise typer.Exit(code=1)
        
        with console.status("📋 データセットカードを生成中..."):
            readme_file = output_file.parent / "README.md"
            create_dataset_card(alpaca_data, readme_file, "Converted QA Dataset")
        
        # Hugging Face Hubにアップロード
        if upload_hf:
            if not hf_repo_name:
                print_error_panel("--hf-repo-nameが指定されていません！\n例: --hf-repo-name username/my-qa-dataset")
                raise typer.Exit(code=1)
            
            with console.status(f"🤗 Hugging Face Hubにアップロード中..."):
                success = upload_to_huggingface(
                    dataset_data=alpaca_data,
                    repo_name=hf_repo_name,
                    hf_token=hf_token if hf_token else None,
                    private=hf_private,
                    commit_message=f"Upload converted QA dataset with {len(alpaca_data)} entries",
                    readme_file=readme_file
                )
            
            if not success:
                print_error_panel("Hugging Faceアップロードに失敗しました")
                raise typer.Exit(code=1)
        
        details = [
            f"{len(alpaca_data)}個のエントリを変換",
            f"出力先: {output_file}",
            f"データセットカード: {readme_file}"
        ]
        if upload_hf and hf_repo_name:
            details.append(f"Hugging Face: {hf_repo_name}")
        
        print_success_summary("Alpaca形式への変換が完了しました！", details)
        
    except Exception as e:
        print_error_panel(f"変換中にエラーが発生しました: {e}")
        raise typer.Exit(code=1)


@app.command()
def aggregate_logs(
    output_dir: Annotated[Path, typer.Argument(
        exists=True, dir_okay=True, readable=True,
        help="logsフォルダが含まれる出力ディレクトリへのパス。"
    )]
):
    """logsフォルダ内のタイムスタンプ付きXMLファイルを集約してqaフォルダのXMLを生成します。"""
    print_logo()
    
    try:
        logs_dir = output_dir / "logs"
        qa_dir = output_dir / "qa"
        
        if not logs_dir.exists():
            print_error_panel(f"logsフォルダが見つかりません: {logs_dir}")
            raise typer.Exit(code=1)
        
        aggregation_table = Table(show_header=False, box=None)
        aggregation_table.add_column("項目", style="bold cyan")
        aggregation_table.add_column("パス", style="white")
        aggregation_table.add_row("📁 logsフォルダ", str(logs_dir))
        aggregation_table.add_row("🎯 出力先", str(qa_dir))
        
        console.print(Panel(aggregation_table, title="[bold blue]📄 ログ集約[/bold blue]", border_style="blue"))
        
        with console.status("🔄 XMLファイルを集約中..."):
            from easy_dataset_cli.core import aggregate_logs_xml_to_qa
            aggregate_logs_xml_to_qa(logs_dir, qa_dir)
        
        print_success_summary("ログ集約が完了しました！", [f"出力先: {qa_dir}"])
        
    except Exception as e:
        print_error_panel(f"エラーが発生しました: {e}")
        raise typer.Exit(code=1)


@app.command(name="help", hidden=True)
def show_help():
    """ヘルプを美しく表示"""
    print_logo()
    console.print(app.get_help(typer.Context(app)))


def _batch_process_files(text_files, ga_file, ga_base_dir, output_dir, model, chunk_size, chunk_overlap,
                        num_qa_pairs, use_fulltext, use_thinking, append_mode,
                        export_alpaca, upload_hf, hf_repo_name, hf_token, hf_private):
    """複数のテキストファイルをバッチ処理する内部関数（各ファイルごとにフォルダを作成）"""
    
    # GAペアの解析は各ファイルごとに行う（ga_base_dirモードの場合）
    ga_pairs = None
    if ga_file:
        with console.status("🔍 GAペアを解析中..."):
            ga_pairs = parse_ga_file(ga_file)

        if not ga_pairs:
            print_error_panel("有効なGAペアが定義ファイルに見つかりませんでした。")
            raise typer.Exit(code=1)

        console.print(f"\n[green]✓[/green] {len(ga_pairs)}個のGAペアを発見しました")

    # モード警告を表示
    warnings = []
    if use_fulltext:
        warnings.append("📋 全文コンテキストモード")
    if use_thinking:
        warnings.append("🤔 思考フローモード")
    
    if warnings:
        warning_panel = Panel(
            "\n".join(warnings) + "\n\n⚠️ 処理時間とAPIコストが増加する可能性があります",
            title="[bold yellow]⚠️ モード警告[/bold yellow]",
            border_style="yellow"
        )
        console.print(warning_panel)

    total_files = len(text_files)
    successful_files = []
    total_qa_pairs_generated = 0
    
    with Progress(console=console) as progress:
        main_task = progress.add_task("[green]ファイルを処理中...", total=total_files)
        
        for file_idx, text_file in enumerate(text_files):
            console.print(f"\n[bold cyan]処理中: {text_file.name}[/bold cyan]")
            
            try:
                # 各ファイルごとに専用フォルダを作成
                file_output_dir = output_dir / text_file.stem
                dirs = create_output_directories(file_output_dir)
                console.print(f"[dim]✓ ファイル用ディレクトリを作成: {file_output_dir}[/dim]")
                
                text = text_file.read_text(encoding="utf-8")
                console.print(f"[dim]✓ テキスト長: {len(text):,} 文字[/dim]")
                
                # GAファイルのパスを決定するロジック
                current_ga_path = None
                if ga_file:
                    # 従来通り、指定された単一のGAファイルを使用
                    current_ga_path = ga_file
                    console.print(f"[dim]✓ 使用するGA定義: {current_ga_path}[/dim]")
                elif ga_base_dir:
                    # 入力ファイル名から対応するGAファイルのパスを組み立てる
                    file_stem = text_file.stem
                    inferred_ga_path = ga_base_dir / file_stem / "ga" / "ga_definitions.xml"
                    
                    if inferred_ga_path.exists():
                        current_ga_path = inferred_ga_path
                        console.print(f"[dim]✓ GA定義を自動検出: {current_ga_path}[/dim]")
                    else:
                        console.print(f"[yellow]警告: {text_file.name} に対応するGA定義が見つかりませんでした。スキップします。[/yellow]")
                        console.print(f"[dim]検索パス: {inferred_ga_path}[/dim]")
                        continue  # 次のファイルへ
                
                # GAペアを解析
                with console.status("🔍 GAペアを解析中..."):
                    current_ga_pairs = parse_ga_file(current_ga_path)
                
                if not current_ga_pairs:
                    console.print(f"[yellow]警告: {text_file.name} のGA定義から有効なGAペアが見つかりませんでした。スキップします。[/yellow]")
                    continue
                
                console.print(f"[green]✓[/green] {len(current_ga_pairs)}個のGAペアを発見")
                
                with console.status(f"✂️ テキストをチャンクに分割中... ({text_file.name})"):
                    chunks = split_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                console.print(f"[green]✓[/green] {len(chunks)}個のチャンクを作成")
                
                all_qa_pairs_with_ga = []
                total_tasks_for_file = len(chunks) * len(current_ga_pairs)
                file_task = progress.add_task(f"[blue]{text_file.name}", total=total_tasks_for_file)

                for chunk in chunks:
                    for ga_pair in current_ga_pairs:
                        if use_thinking:
                            qa_pairs = generate_qa_for_chunk_with_ga_and_thinking(
                                chunk=chunk,
                                full_text=text if use_fulltext else "",
                                model=model,
                                ga_pair=ga_pair,
                                logs_dir=dirs["logs"],
                                num_qa_pairs=num_qa_pairs
                            )
                        elif use_fulltext:
                            qa_pairs = generate_qa_for_chunk_with_ga_and_fulltext(
                                chunk=chunk,
                                full_text=text,
                                model=model,
                                ga_pair=ga_pair,
                                logs_dir=dirs["logs"],
                                num_qa_pairs=num_qa_pairs
                            )
                        else:
                            qa_pairs = generate_qa_for_chunk_with_ga(
                                chunk, model=model, ga_pair=ga_pair,
                                logs_dir=dirs["logs"],
                                num_qa_pairs=num_qa_pairs
                            )

                        for pair in qa_pairs:
                            qa_entry = {
                                "genre": ga_pair['genre']['title'],
                                "audience": ga_pair['audience']['title'],
                                "question": pair['question'],
                                "answer": pair['answer']
                            }
                            all_qa_pairs_with_ga.append(qa_entry)

                        progress.update(
                            file_task, advance=1,
                            description=f"Genre: {ga_pair['genre']['title']}"
                        )
                
                progress.remove_task(file_task)
                
                # このファイルのQ&AペアをXMLに変換して保存
                xml_outputs_by_genre = convert_to_xml_by_genre(all_qa_pairs_with_ga, dirs["qa"], append_mode)
                
                saved_files = []
                for genre, xml_content in xml_outputs_by_genre.items():
                    safe_genre_name = sanitize_filename(genre)
                    output_file_path = dirs["qa"] / f"{safe_genre_name}.xml"
                    output_file_path.write_text(xml_content, encoding="utf-8")
                    saved_files.append(output_file_path.name)
                
                # アルパカ形式でのエクスポート（ファイル個別）
                if export_alpaca:
                    alpaca_file = dirs["base"] / "dataset_alpaca.json"
                    alpaca_data = convert_all_xml_to_alpaca(dirs["qa"], alpaca_file)
                    
                    # データセットカードを生成
                    readme_file = dirs["base"] / "README.md"
                    create_dataset_card(alpaca_data, readme_file, f"Generated QA Dataset from {text_file.name}")
                
                successful_files.append((text_file.name, file_output_dir, len(all_qa_pairs_with_ga), saved_files))
                total_qa_pairs_generated += len(all_qa_pairs_with_ga)
                console.print(f"[green]✓[/green] {len(all_qa_pairs_with_ga)}個のQ&Aペアを生成")
                
            except Exception as e:
                console.print(f"[red]エラー: {text_file.name} の処理に失敗しました: {e}[/red]")
                continue
            
            progress.update(
                main_task, advance=1,
                description=f"完了: {text_file.name}"
            )

    if not successful_files:
        print_error_panel("有効なQ&Aペアが生成されませんでした。")
        raise typer.Exit(code=1)

    # 成功メッセージを美しく表示
    details = [
        f"{total_qa_pairs_generated}個のQ&Aペアを生成",
        f"処理済みファイル: {len(successful_files)}/{total_files}個",
        f"各ファイルごとに専用フォルダを作成"
    ]
    
    # 処理されたファイル一覧を表示
    files_table = Table(show_header=True, box=None)
    files_table.add_column("ファイル", style="cyan")
    files_table.add_column("フォルダ", style="white")  
    files_table.add_column("Q&Aペア数", style="green")
    
    for file_name, output_path, qa_count, _ in successful_files:
        files_table.add_row(file_name, str(output_path), str(qa_count))
    
    console.print(Panel(files_table, title="[bold green]📄 処理結果[/bold green]", border_style="green"))
    
    print_success_summary("バッチQ&A生成が完了しました！", details)
    
    # Hugging Face Hubへのアップロード処理（最初の成功ファイルのみ、またはユーザーが個別指定）
    if upload_hf and export_alpaca:
        if not hf_repo_name:
            console.print("[bold red]--hf-repo-nameが指定されていません！[/bold red]")
            console.print("[yellow]例: --hf-repo-name username/my-qa-dataset[/yellow]")
        else:
            console.print(f"\n[bold blue]Hugging Face Hub アップロードについて[/bold blue]")
            console.print("[yellow]注意: 現在は各ファイルが個別のフォルダに保存されているため、")
            console.print("個別にアップロードするか、統合してアップロードするかを選択してください。[/yellow]")


def _batch_create_ga_files(text_files, output_dir, model, num_ga_pairs):
    """複数のテキストファイルからGAペアをバッチ生成する内部関数（各ファイルごとにフォルダを作成）"""
    
    total_files = len(text_files)
    successful_files = []
    
    with Progress(console=console) as progress:
        main_task = progress.add_task("[green]GAペアを生成中...", total=total_files)
        
        for file_idx, text_file in enumerate(text_files):
            console.print(f"\n[bold cyan]処理中: {text_file.name}[/bold cyan]")
            
            try:
                # 各ファイルごとに専用フォルダを作成
                file_output_dir = output_dir / text_file.stem
                dirs = create_output_directories(file_output_dir)
                console.print(f"[dim]✓ ファイル用ディレクトリを作成: {file_output_dir}[/dim]")
                
                text = text_file.read_text(encoding="utf-8")
                console.print(f"[dim]✓ テキスト長: {len(text):,} 文字[/dim]")

                with console.status(f"[bold green]🤖 LLMにGAペアの提案を依頼中... ({text_file.name})[/bold green]"):
                    xml_content = generate_ga_definitions(text, model=model, num_ga_pairs=num_ga_pairs)

                # LLMのrawレスポンスをlogsディレクトリに保存
                raw_file_path = dirs["logs"] / "raw.md"
                raw_file_path.write_text(xml_content, encoding="utf-8")
                console.print(f"[green]✓[/green] LLMのrawレスポンスを保存: [cyan]{raw_file_path}[/cyan]")

                with console.status(f"[bold green]🔍 XMLからGAペアを解析中... ({text_file.name})[/bold green]"):
                    # XMLからGAペアを解析
                    ga_pairs = parse_ga_definitions_from_xml(xml_content)
                
                if not ga_pairs:
                    console.print(f"[yellow]警告: {text_file.name} からは有効なGAペアが生成されませんでした[/yellow]")
                    continue

                # 元のXMLファイルをgaディレクトリに保存（クリーンなXMLのみ）
                xml_file_path = dirs["ga"] / "ga_definitions.xml"
                xml_start = xml_content.find("<GADefinitions>")
                xml_end = xml_content.rfind("</GADefinitions>")
                if xml_start != -1 and xml_end != -1:
                    clean_xml = xml_content[xml_start: xml_end + len("</GADefinitions>")]
                    xml_file_path.write_text(clean_xml, encoding="utf-8")
                    console.print(f"[green]✓[/green] GA定義XMLファイルを保存: [cyan]{xml_file_path}[/cyan]")

                # Genreごとにマークダウンファイルをgaディレクトリに保存
                save_ga_definitions_by_genre(ga_pairs, dirs["ga"])
                
                successful_files.append((text_file.name, file_output_dir, len(ga_pairs)))
                console.print(f"[green]✓[/green] {len(ga_pairs)}個のGAペアを生成しました")
                
            except Exception as e:
                console.print(f"[red]エラー: {text_file.name} の処理に失敗しました: {e}[/red]")
                continue
            
            progress.update(
                main_task, advance=1,
                description=f"完了: {text_file.name}"
            )

    if not successful_files:
        print_error_panel("有効なGAペアが生成されませんでした。\n生成されたXMLの内容を確認してください。")
        raise typer.Exit(code=1)

    # 成功メッセージを美しく表示
    total_ga_pairs = sum(count for _, _, count in successful_files)
    details = [
        f"{total_ga_pairs}個のGAペアを生成",
        f"処理済みファイル: {len(successful_files)}/{total_files}個",
        f"各ファイルごとに専用フォルダを作成"
    ]
    
    # 処理されたファイル一覧を表示
    files_table = Table(show_header=True, box=None)
    files_table.add_column("ファイル", style="cyan")
    files_table.add_column("フォルダ", style="white")
    files_table.add_column("GAペア数", style="green")
    
    for file_name, output_path, ga_count in successful_files:
        files_table.add_row(file_name, str(output_path), str(ga_count))
    
    console.print(Panel(files_table, title="[bold green]📄 処理結果[/bold green]", border_style="green"))
    
    print_success_summary("バッチGAペア生成が完了しました！", details)
    
    next_steps_panel = Panel(
        "🔍 生成されたファイルをレビュー\n"
        "✏️ 必要に応じて編集\n"
        "🚀 `generate` コマンドでQ&A生成へ",
        title="[bold yellow]🔄 次のステップ[/bold yellow]",
        border_style="yellow"
    )
    console.print(next_steps_panel)


def main():
    """メイン関数 - ヘルプ時にロゴを表示"""
    import sys
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]):
        print_logo()
    app()


if __name__ == "__main__":
    main()
