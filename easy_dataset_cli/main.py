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
    convert_to_xml_by_genre,
    generate_ga_definitions
)

# .envファイルを読み込む
load_dotenv()

app = typer.Typer(
    help="テキストファイルからQ&Aペアを生成するシンプルなCLIツール。",
    context_settings={"help_option_names": ["-h", "--help"]}
)
console = Console()


def sanitize_filename(name: str) -> str:
    """ファイル名として安全な文字列に変換する"""
    return "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).rstrip()


@app.command()
def create_ga(
    file_path: Annotated[Path, typer.Argument(
        exists=True, dir_okay=False, readable=True,
        help="GAペアの定義を生成するための元のテキストファイル。"
    )],
    output_path: Annotated[Path, typer.Option(
        "--output", "-o", writable=True,
        help="生成されたGAペア定義（Markdown）を保存するファイルパス。"
    )],
    model: Annotated[str, typer.Option(
        "--model", "-m",
        help="GAペア定義の生成に使用するLLMモデル名。"
    )] = "openrouter/openai/gpt-4o",
):
    """元の文章を分析し、GAペア定義のMarkdownファイルを生成します。"""
    console.print(f"ファイルを読み込んでいます: [cyan]{file_path}[/cyan]")

    try:
        text = file_path.read_text(encoding="utf-8")

        with console.status("[bold green]LLMに最適なGAペアを提案させています..."):
            markdown_content = generate_ga_definitions(text, model=model)

        output_path.write_text(markdown_content, encoding="utf-8")

        console.print(
            f"\n[bold green]✓[/bold green] GAペア定義ファイルを "
            f"[cyan]{output_path}[/cyan] に正常に保存しました。"
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
        help="Genre-Audienceペアを定義したMarkdownファイルへのパス。"
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
):
    """テキストファイルとGA定義からQ&Aペアを生成し、Genre別のXMLファイルとして出力します。"""
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

        with Progress(console=console) as progress:
            task = progress.add_task("[green]Q&Aペアを生成中...", total=total_tasks)

            for chunk in chunks:
                for ga_pair in ga_pairs:
                    qa_pairs = generate_qa_for_chunk_with_ga(
                        chunk, model=model, ga_pair=ga_pair
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

        xml_outputs_by_genre = convert_to_xml_by_genre(all_qa_pairs_with_ga)

        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            console.print(f"XMLファイルを [cyan]{output_dir}[/cyan] に保存しています...")

            for genre, xml_content in xml_outputs_by_genre.items():
                safe_genre_name = sanitize_filename(genre)
                output_file_path = output_dir / f"{safe_genre_name}.xml"
                output_file_path.write_text(xml_content, encoding="utf-8")
                console.print(f"  - [green]✓[/green] {output_file_path.name}")

            console.print("\n[bold green]すべてのファイルの保存が完了しました。[/bold green]")
        else:
            console.print("\n--- 生成されたQ&Aペア (Genre別XML) ---")
            for genre, xml_content in xml_outputs_by_genre.items():
                console.print(f"\n[bold yellow]## Genre: {genre} ##[/bold yellow]")
                console.print(xml_content, overflow="fold")
    
    except Exception as e:
        console.print(f"[bold red]エラーが発生しました:[/bold red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()