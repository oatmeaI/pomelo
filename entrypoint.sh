cd /
caddy start
cd /pomelo || exit
poetry install
source .venv/bin/activate
poetry run start
