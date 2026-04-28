import concurrent.futures
import feedparser
import re
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup

@st.cache_data(ttl=3600)
def get_posts():
    posts = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    def fetch_month(year, month):
        month_posts = []
        page = 1
        unique_links = set()
        while True:
            if page == 1:
                url = f"https://ameblo.jp/amnn1/archive-{year}{month:02d}.html"
            else:
                url = f"https://ameblo.jp/amnn1/archive{page}-{year}{month:02d}.html"

            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code != 200:
                    break

                soup = BeautifulSoup(response.content, 'lxml')
                items = [a for a in soup.select('a') if 'href' in a.attrs and 'entry-' in a['href'] and a.text.strip()]

                new_items_found = False
                for item in items:
                    title = item.text.strip()
                    link = item['href']
                    if link and link.startswith('/'):
                        link = f"https://ameblo.jp{link}"

                    if link not in unique_links:
                        unique_links.add(link)
                        new_items_found = True

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
                            date = f"{year}年{date_match.group(1)}"

                        month_posts.append({
                            '日付': date,
                            '番組': program,
                            'URL': link,
                            'タイトル': title,
                            'sort_key': f"{year}{month:02d}"
                        })

                if not new_items_found:
                    break

                next_page = False
                for a in soup.find_all('a'):
                    if '次' in a.text:
                        next_page = True
                        break

                if not next_page:
                    break

                page += 1
            except Exception as e:
                break
        return month_posts

    years = [2026, 2025]
    months = list(range(12, 0, -1))

    tasks = [(y, m) for y in years for m in months]

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(lambda args: fetch_month(*args), tasks)

    for month_posts in results:
        posts.extend(month_posts)

    seen_urls = set()
    deduped_posts = []
    for p in posts:
        if p['URL'] not in seen_urls:
            seen_urls.add(p['URL'])
            deduped_posts.append(p)

    return deduped_posts


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
