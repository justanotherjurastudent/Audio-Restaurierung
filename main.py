"""
Audio-Restaurationstool v0.6.8 - Refaktorierte Version

Copyright (C) 2025 [Lukas Collier]

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import sys
from typing import NoReturn
from gui.main_window import AudioRestorerMainWindow
from utils.validators import check_dependencies

def main() -> NoReturn:
    """Haupteinstiegspunkt der Anwendung"""
    print("🎵 Audio-Restaurationstool v0.6.8 wird gestartet...")
    
    # Abhängigkeiten prüfen
    if not check_dependencies():
        sys.exit(1)
    
    # GUI starten
    app = AudioRestorerMainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
