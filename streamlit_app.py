from pathlib import Path
import runpy


APP_PATH = Path(__file__).parent / "frontend" / "combined_app.py"

runpy.run_path(str(APP_PATH), run_name="__main__")
