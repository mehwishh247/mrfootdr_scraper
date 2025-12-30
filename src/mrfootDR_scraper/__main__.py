import asyncio
from .core import run_scraper

def main():
    asyncio.run(run_scraper())

if __name__ == "__main__":
    main()
    