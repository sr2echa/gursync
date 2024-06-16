import typer
import questionary
from gursync import config, sync

app = typer.Typer()

@app.command()
def setup():
    api_key = questionary.text("Enter your Imgur API Key:").ask()
    config.set_api_key(api_key)
    typer.echo("API Key saved!")

@app.command()
def create():
    api_key = config.get_api_key()
    if not api_key:
        typer.echo("API Key not set. Please run 'gursync setup' to configure it.")
        raise typer.Abort()
    
    album_id = questionary.text("Enter the Imgur Album ID:").ask()
    directory = questionary.path("Enter the directory to sync (default is current directory):", default='.').ask()
    
    cfg = config.load_config()
    if 'sync_pairs' not in cfg:
        cfg['sync_pairs'] = []
    cfg['sync_pairs'].append({'album_id': album_id, 'directory': directory})
    config.save_config(cfg)
    
    typer.echo(f"Sync pair created: Album {album_id} <-> Directory {directory}")

@app.command()
def start():
    api_key = config.get_api_key()
    if not api_key:
        typer.echo("API Key not set. Please run 'gursync setup' to configure it.")
        raise typer.Abort()
    
    sync.start_sync()

if __name__ == "__main__":
    app()
