import asyncio

from app.db.database import create_db_schema


async def main() -> None:
    await create_db_schema()


if __name__ == "__main__":
    asyncio.run(main())
