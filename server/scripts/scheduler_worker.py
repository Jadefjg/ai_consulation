"""独立定时任务进程。"""
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from core.config import settings
from core.logging import configure_logging
from services.scheduler import expired_appointment_worker

configure_logging(settings.log_level)


async def main() -> None:
    await expired_appointment_worker(asyncio.Event())


if __name__ == "__main__":
    asyncio.run(main())
