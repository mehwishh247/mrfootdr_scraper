# MrFootDr Clinics Contact Information Scraper

This scraper is designed to scrape contact information from [MrFoorDr Clinics Website](https://www.myfootdr.com.au). The scraper extract clinic's name, phone number, email address, and service provided by the certain clinic location.

## Dependencies

The scraper require only one external dependency: 
* Pydoll

1. You can install Pydoll using following commands:
```
pip install pydoll-python
```
or 
```
pip install .
```

2. Using uv or poetry 
```
poetry sync
uv sync
```

## Deployment

To run the scraper, run the following command in terminal
```
uv run python -m mrfootDR_scraper
```
or

```
poetry run python -m mrfootDR_scraper
```