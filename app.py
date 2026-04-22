import feedparser
import re
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup

@st.cache_data(ttl=3600)
def get_posts():
    # To get a more comprehensive history rather than just the last 20 from RSS,
    # we can try to scrape a few pages of entrylist.
    # However, since we don't want to over-scrape, we'll try to fetch a few pages.
    # Actually, let's keep the RSS for simplicity as it's much more robust and we can fall back to it,
    # but the reviewer noted RSS feed only contains recent 15-20 entries. Let's write a scraper for the entry list.

    posts = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    base_url = "https://ameblo.jp/amnn1/entrylist"

    # Let's scrape the first 5 pages (up to 100 entries) to get a better history
    for page in range(1, 6):
        url = f"{base_url}-{page}.html" if page > 1 else f"{base_url}.html"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                break
            soup = BeautifulSoup(response.content, 'lxml')

            # Find the title links in the entry list
            items = soup.select('h2[data-uranus-component="entryItemTitle"] a')
            if not items:
                break

            for item in items:
                title = item.text.strip()
                link = item.get('href')
                if link and link.startswith('/'):
                    link = f"https://ameblo.jp{link}"

                program = "その他"
                if "ラジオ英会話" in title:
                    program = "ラジオ英会話"
                elif "ビジネス英語" in title:
                    program = "ラジオビジネス英語"
                elif "現代英語" in title:
                    program = "現代英語"
                elif "タイムトライアル" in title:
                    program = "タイムトライアル"

                date = ""
                date_match = re.search(r'(\d+月\d+日)', title)
                if date_match:
                    date = date_match.group(1)

                posts.append({
                    '日付': date,
                    '番組': program,
                    'URL': link,
                    'タイトル': title
                })
        except Exception as e:
            # st.warning(f"Error fetching page {page}: {e}")
            break

    # Fallback to RSS if scraping failed completely
    if not posts:
        url = "https://rssblog.ameba.jp/amnn1/rss20.xml"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            feed = feedparser.parse(response.content)
            for entry in feed.entries:
                title = entry.title
                link = entry.link

                program = "その他"
                if "ラジオ英会話" in title:
                    program = "ラジオ英会話"
                elif "ビジネス英語" in title:
                    program = "ラジオビジネス英語"
                elif "現代英語" in title:
                    program = "現代英語"
                elif "タイムトライアル" in title:
                    program = "タイムトライアル"

                date = ""
                date_match = re.search(r'(\d+月\d+日)', title)
                if date_match:
                    date = date_match.group(1)

                posts.append({
                    '日付': date,
                    '番組': program,
                    'URL': link,
                    'タイトル': title
                })
        except Exception as e:
            st.error(f"Failed to fetch data: {e}")

    return posts

def main():
    st.set_page_config(page_title="NHK英語スクリプト集", page_icon="📻", layout="wide")
    st.title("📻 NHK英語スクリプト集 (amnn1のブログ)")

    st.markdown("""
    [amnn1のブログ](https://ameblo.jp/amnn1/)の過去のスクリプトを一覧表示します。
    特定の放送日と番組から目的のスクリプトを探しやすくしています。
    """)

    with st.spinner('データを取得中...'):
        posts = get_posts()

    if not posts:
        st.warning("データが見つかりませんでした。")
        return

    df = pd.DataFrame(posts)

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        programs = ["すべて"] + list(df['番組'].unique())
        selected_program = st.selectbox("番組で絞り込み", programs)
    with col2:
        dates = ["すべて"] + list(df[df['日付'] != '']['日付'].unique())
        selected_date = st.selectbox("日付で絞り込み", dates)

    # Apply filters
    filtered_df = df.copy()
    if selected_program != "すべて":
        filtered_df = filtered_df[filtered_df['番組'] == selected_program]
    if selected_date != "すべて":
        filtered_df = filtered_df[filtered_df['日付'] == selected_date]

    st.markdown(f"**{len(filtered_df)}** 件のスクリプトが見つかりました。")

    st.dataframe(
        filtered_df,
        column_config={
            "URL": st.column_config.LinkColumn("ブログリンク", display_text="リンクを開く"),
            "タイトル": st.column_config.TextColumn("タイトル", width="large")
        },
        hide_index=True,
        width='stretch'
    )

if __name__ == "__main__":
    main()
