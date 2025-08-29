#!/usr/bin/env python3
"""
バッチ処理機能
"""

from pathlib import Path
from rich.console import Console
from rich.progress import Progress

from .core import (
    parse_ga_file,
    split_text,
    get_chunk_with_surrounding_context,
    create_augmented_chunks,
    convert_to_xml_by_genre,
    create_output_directories
)
from .ga_parser import parse_ga_definitions_from_xml_improved

# generatorsパッケージからインポート
from .generators import (
    generate_qa_for_chunk_with_ga,
    generate_qa_for_chunk_with_ga_and_fulltext,
    generate_qa_for_chunk_with_ga_and_thinking,
    generate_qa_for_chunk_with_surrounding_context,
    generate_ga_definitions
)

console = Console()


def _batch_create_ga_files(text_files, output_dir, model, num_ga_pairs, max_context_length=8000):
    """複数のテキストファイルからGAペアをバッチ生成する内部関数（各ファイルごとにフォルダを作成）"""

    from .core import create_output_directories, save_ga_definitions_by_genre, parse_ga_definitions_from_xml

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
                    xml_content = generate_ga_definitions(text, model=model, num_ga_pairs=num_ga_pairs, max_context_length=max_context_length)

                # LLMのrawレスポンスをlogsディレクトリに保存
                raw_file_path = dirs["logs"] / "raw.md"
                raw_file_path.write_text(xml_content, encoding="utf-8")
                console.print(f"[green]✓[/green] LLMのrawレスポンスを保存: [cyan]{raw_file_path.name}[/cyan]")

                with console.status(f"[bold green]🔍 XMLからGAペアを解析中... ({text_file.name})[/bold green]"):
                    # XMLからGAペアを解析（改良版）
                    ga_pairs = parse_ga_definitions_from_xml_improved(xml_content)

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
    from rich.table import Table
    files_table = Table(show_header=True, box=None)
    files_table.add_column("ファイル", style="cyan")
    files_table.add_column("フォルダ", style="white")
    files_table.add_column("GAペア数", style="green")

    for file_name, output_path, ga_count in successful_files:
        files_table.add_row(file_name, str(output_path), str(ga_count))

    console.print(Table(title="[bold green]📄 処理結果[/bold green]", box=True))
    console.print(files_table)

    from .commands import print_success_summary
    print_success_summary("バッチGAペア生成が完了しました！", details)

    from .commands import Panel
    next_steps_panel = Panel(
        "🔍 生成されたファイルをレビュー\n"
        "✏️ 必要に応じて編集\n"
        "🚀 `generate` コマンドでQ&A生成へ",
        title="[bold yellow]🔄 次のステップ[/bold yellow]",
        border_style="yellow"
    )
    console.print(next_steps_panel)


def _batch_process_files(text_files, ga_file, ga_base_dir, output_dir, model, chunk_size, chunk_overlap,
                        num_qa_pairs, use_fulltext, use_thinking, use_surrounding_context,
                        context_before, context_after, append_mode,
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
    if use_surrounding_context:
        warnings.append(f"🔗 周辺チャンクモード ({context_before}前+{context_after}後)")

    if warnings:
        from .commands import Panel
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

                # 周辺コンテキストモードの場合、チャンクを拡張
                if use_surrounding_context:
                    with console.status(f"🔗 周辺コンテキストを生成中... ({text_file.name})"):
                        augmented_chunks = create_augmented_chunks(chunks, context_before, context_after)
                    console.print(f"[green]✓[/green] {len(augmented_chunks)}個の拡張チャンクを作成")

                all_qa_pairs_with_ga = []
                total_tasks_for_file = len(chunks) * len(current_ga_pairs)
                file_task = progress.add_task(f"[blue]{text_file.name}", total=total_tasks_for_file)

                if use_surrounding_context:
                    # 周辺コンテキストモードの処理
                    # ドキュメント冒頭（最大3000文字）を付与して文脈の安定性を高める
                    doc_head = text[:3000]
                    for i, (target_chunk, augmented_content, _) in enumerate(augmented_chunks):
                        for ga_pair in current_ga_pairs:
                            content_with_head = (
                                f"【ドキュメント冒頭（最大3000文字）】:\n{doc_head}\n\n" +
                                augmented_content
                            )
                            qa_pairs = generate_qa_for_chunk_with_surrounding_context(
                                content=content_with_head,
                                model=model,
                                ga_pair=ga_pair,
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
                else:
                    # 通常モードの処理
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
                    from .core import sanitize_filename
                    safe_genre_name = sanitize_filename(genre)
                    output_file_path = dirs["qa"] / f"{safe_genre_name}.xml"
                    output_file_path.write_text(xml_content, encoding="utf-8")
                    saved_files.append(output_file_path.name)

                # アルパカ形式でのエクスポート（ファイル個別）
                if export_alpaca:
                    from .core import convert_all_xml_to_alpaca, create_dataset_card
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
        from .commands import print_error_panel
        print_error_panel("有効なQ&Aペアが生成されませんでした。")
        import typer
        raise typer.Exit(code=1)

    # 成功メッセージを美しく表示
    details = [
        f"{total_qa_pairs_generated}個のQ&Aペアを生成",
        f"処理済みファイル: {len(successful_files)}/{total_files}個",
        f"各ファイルごとに専用フォルダを作成"
    ]

    # 処理されたファイル一覧を表示
    from rich.table import Table
    files_table = Table(show_header=True, box=None)
    files_table.add_column("ファイル", style="cyan")
    files_table.add_column("フォルダ", style="white")
    files_table.add_column("Q&Aペア数", style="green")

    for file_name, output_path, qa_count, _ in successful_files:
        files_table.add_row(file_name, str(output_path), str(qa_count))

    console.print(Table(title="[bold green]📄 処理結果[/bold green]", box=True))
    console.print(files_table)

    from .commands import print_success_summary
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


def print_error_panel(error_msg: str):
    """エラーメッセージを美しく表示"""
    panel = f"[bold red]❌ エラー[/bold red]\n{error_msg}"
    console.print(panel)
