# Ameba Blog Scraper

This is a Streamlit application that scrapes the RSS feed of the Ameba blog at `https://ameblo.jp/amnn1/` and displays the posts in a table format.

## Features
- Fetches the RSS feed from `https://rssblog.ameba.jp/amnn1/rss20.xml`
- Extracts the date, program name, and URL from each post
- Displays the data in an interactive table using Streamlit
- Clickable URLs for easy access to the blog posts

## Prerequisites
- Python 3.12+
- Packages listed in `requirements.txt`

## Running the application
```bash
streamlit run app.py
```
