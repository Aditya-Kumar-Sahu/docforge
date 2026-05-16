import typer
from rich.console import Console

console = Console()
app = typer.Typer()


@app.command()
def hello(name: str = "World") -> None:
    console.print(f"[bold green]Hello[/bold green] {name}!")


if __name__ == "__main__":
    app()
