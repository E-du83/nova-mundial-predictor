from pathlib import Path
from storage.database import init_db

ROOT = Path(__file__).resolve().parents[1]
db_path = ROOT / "nova_mundial_predictor.sqlite3"

created = init_db(db_path)
print(f"Base de datos creada/lista: {created}")