"""AX Analysis worker entry point."""

from __future__ import annotations

import logging

from ax_worker.consumer import run_consumer


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    run_consumer()


if __name__ == "__main__":
    main()
