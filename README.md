# Lichtkrant Client (CLI)

The terminal based client for all online lichtkrant games, alternative to lichtkrant client (old)

## Installation
```bash
git clone git@github.com:djoamersfoort/lichtkrant-client-cli.git
cd lichtkrant-client-cli
python -m venv ENV
source ./ENV/bin/activate
pip install -r requirements.txt
```
After this, you can run it with `python3 main.py`. If the pip install gives you some kind of python execution error, you might need to install the python development package: python-dev or python-devel.

## Testing new clients

When creating a new game for lichtkrant, new clients should be pushed to the [lichtkrant-client repo](https://github.com/djoamersfoort/lichtkrant-client), but for testing you can use developer mode. Enabling developer mode disables updates of the game index, allowing it to be edited. Developer mode is enabled with `python3 main.py true`