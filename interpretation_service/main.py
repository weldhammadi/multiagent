"""
Point d'entrée principal pour lancer une petite démo locale.

Tu peux le lancer avec :
    python -m interpretation_service.main
ou
    python main.py   (si tu es dans le bon dossier PYTHONPATH)
"""

import asyncio

from interpretation_service.infrastructure.logging_config import configure_logging
from interpretation_service.interfaces.cli.simulate_request import run_simulation


def main() -> None:
    configure_logging()
    asyncio.run(run_simulation())


if __name__ == "__main__":
    main()

