import streamlit.web.cli as stcli
import os
import sys

if __name__ == "__main__":
    # Détermine où se trouve app.py (dans le .exe ou dans le dossier normal)
    if getattr(sys, 'frozen', False):
        script_path = os.path.join(sys._MEIPASS, "app.py")
    else:
        script_path = "app.py"
        
    # Lance la commande Streamlit pour exécuter app.py
    sys.argv = ["streamlit", "run", script_path, "--global.developmentMode=false", "--browser.gatherUsageStats=false"]
    sys.exit(stcli.main())