import requests
from bs4 import BeautifulSoup
import datetime
import json
import os
from email.utils import parsedate_to_datetime
import re

# ==========================================
# 1. CẤU HÌNH ĐA NGUỒN DỮ LIỆU
# ==========================================
CAFEF_SOURCES = {
    "CF - Chứng khoán": "https://cafef.vn/thi-truong-chung-khoan.chn",
    "CF - Bất động sản": "https://cafef.vn/bat-dong-san.chn",
    "CF - Doanh nghiệp": "https://cafef.vn/doanh-nghiep.chn",
    "CF - Ngân hàng": "https://cafef.vn/tai-chinh-ngan-hang.chn",
    "CF - Vĩ mô": "https://cafef.vn/vi-mo-dau-tu.chn"
}

# Bổ sung thêm các đầu báo tài chính uy tín khác qua cổng RSS
RSS_SOURCES = {
    "VnEco - Chứng khoán": "https://vneconomy.vn/rss/chung-khoan.rss",
    "VnEco - Bất động sản": "https://vneconomy.vn/rss/bat-dong-san.rss",
    "TinNhanh - Chứng khoán": "https://www.tinnhanhchungkhoan.vn/rss/chung-khoan-113.rss",
    "TinNhanh - Doanh nghiệp": "https://www.tinnhanhchungkhoan.vn/rss/doanh-nghiep-21.rss"
}

DB_FILE = 'news_database.json'

# ==========================================
# 2. LÕI NLP PHÂN TÍCH CẢM XÚC (LEXICON ENGINE)
# ==========================================
POS_WORDS = ['lãi', 'tăng', 'bứt phá', 'vượt', 'kỷ lục', 'khởi sắc', 'phê duyệt', 'hút tiền', 'kỳ vọng', 'tích cực', 'trúng thầu', 'khôi phục', 'chấp thuận', 'tăng trưởng', 'chia cổ tức', 'bùng nổ']
NEG_WORDS = ['lỗ', 'giảm', 'sập', 'thủng', 'bán tháo', 'khởi tố', 'bắt giam', 'cảnh báo', 'rủi ro', 'lao dốc', 'đình chỉ', 'hủy niêm yết', 'phạt', 'trễ hẹn', 'khó khăn', 'thanh tra', 'bốc hơi', 'vi phạm']

def analyze_sentiment(title):
    text = title.lower()
    
    pos_score = sum(1 for word in POS_WORDS if re.search(r'\b' + word + r'\b', text))
    neg_score = sum(1 for word in NEG_WORDS if re.search(r'\b' + word + r'\b', text))
    
    if pos_score > neg_score:
        return "TÍCH CỰC", "#10B981", "rgba(16, 185, 129, 0.15)" # Xanh lá
    elif neg_score > pos_score:
        return "TIÊU CỰC", "#EF4444", "rgba(239, 68, 68, 0.15)" # Đỏ
    else:
        return "TRUNG LẬP", "#6B7280", "rgba(107, 114, 128, 0.1)" # Xám

# ==========================================
# 3. CỖ MÁY CÀO DỮ LIỆU KÉP (HTML + RSS)
# ==========================================
def parse_time(date_str):
    try:
        return parsedate_to_datetime(date_str).timestamp()
    except:
        return 0

def fetch_and_update_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try: db_news = json.load(f)
            except: db_news = []
    else:
        db_news = []

    seen_links = {item.get('link', '') for item in db_news}
    new_articles = []
    
    utc_now = datetime.datetime.utcnow()
    vn_time = utc_now + datetime.timedelta(hours=7)
    fake_time_str = vn_time.strftime("%a, %d %b %Y %H:%M:%S")
    current_ts = vn_time.timestamp()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/114.0.0.0'}

    # 3.1 Cào CafeF qua HTML
    for cat_name, url in CAFEF_SOURCES.items():
        try:
            response = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.find_all('a')
            count = 0
            for a in links:
                if count >= 10: break
                href = a.get('href', '')
                title = a.get('title', '').strip() or a.text.strip()
                if href.endswith('.chn') and len(title) > 20:
                    if href.startswith('/'): href = 'https://cafef.vn' + href
                    if href not in seen_links:
                        sentiment, text_color, bg_color = analyze_sentiment(title)
                        new_articles.append({
                            "category": cat_name, "title": title, "time": fake_time_str,
                            "timestamp": current_ts, "link": href,
                            "sentiment": sentiment, "color": text_color, "bg_color": bg_color
                        })
                        seen_links.add(href)
                        count += 1; current_ts -= 1
        except Exception as e: print(f"Lỗi CafeF {cat_name}: {e}")

    # 3.2 Cào VnEconomy & TinNhanh qua RSS
    for cat_name, url in RSS_SOURCES.items():
        try:
            response = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.content, features="xml")
            items = soup.findAll('item')
            for item in items[:10]:
                link = item.link.text if item.link else ""
                if link not in seen_links and link != "":
                    title = item.title.text if item.title else ""
                    pub_date = item.pubDate.text if item.pubDate else fake_time_str
                    ts = parse_time(pub_date) or current_ts
                    sentiment, text_color, bg_color = analyze_sentiment(title)
                    new_articles.append({
                        "category": cat_name, "title": title, "time": pub_date.replace("+0700", "").strip(),
                        "timestamp": ts, "link": link,
                        "sentiment": sentiment, "color": text_color, "bg_color": bg_color
                    })
                    seen_links.add(link)
                    current_ts -= 1
        except Exception as e: print(f"Lỗi RSS {cat_name}: {e}")

    updated_db = new_articles + db_news
    updated_db.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    updated_db = updated_db[:800]
    
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(updated_db, f, ensure_ascii=False, indent=4)
        
    return updated_db

# ==========================================
# 4. XUẤT GIAO DIỆN WEB (CÓ TAG CẢM XÚC AI)
# ==========================================
def generate_html(news_list):
    utc_now = datetime.datetime.utcnow()
    vn_time = utc_now + datetime.timedelta(hours=7)
    now_str = vn_time.strftime("%d/%m/%Y %H:%M:%S")
    
    # Gộp tất cả các nguồn thành bộ lọc danh mục
    ALL_CATEGORIES = list(CAFEF_SOURCES.keys()) + list(RSS_SOURCES.keys())
    
    tabs_html = f'<button class="tab-btn active" onclick="openTab(event, \'tab_ALL\')">Tất cả tin tức</button>\n'
    for idx, cat_name in enumerate(ALL_CATEGORIES):
        tabs_html += f'<button class="tab-btn" onclick="openTab(event, \'tab_{idx}\')">{cat_name}</button>\n'

    def create_card(item):
        cat = item.get('category', 'Chung')
        title = item.get('title', 'Không có tiêu đề')
        link = item.get('link', '#')
        sent = item.get('sentiment', 'TRUNG LẬP')
        t_col = item.get('color', '#6B7280')
        b_col = item.get('bg_color', 'rgba(107, 114, 128, 0.1)')
        
        raw_time = item.get('time', '')
        parts = raw_time.split(' ')
        if len(parts) >= 5: display_time = f"{parts[4][:5]} ({parts[1]}/{parts[2]})"
        else: display_time = raw_time
            
        return f"""
            <div class="news-card">
                <h2 class="news-title"><a href="{link}" target="_blank">{title}</a></h2>
                <div class="news-meta">
                    <span class="category-badge">{cat}</span>
                    <span class="sentiment-badge" style="color:{t_col}; background:{b_col}; border: 1px solid {t_col}30;">{sent}</span>
                    <span style="margin-left: auto;">🕒 {display_time}</span>
                </div>
            </div>
        """

    content_html = f'<div id="tab_ALL" class="tab-content active">\n'
    if not news_list: content_html += '<div class="empty-msg">Hệ thống đang thu thập dữ liệu đa nguồn...</div>'
    for item in news_list[:200]: content_html += create_card(item)
    content_html += '</div>\n'

    for idx, cat_name in enumerate(ALL_CATEGORIES):
        content_html += f'<div id="tab_{idx}" class="tab-content">\n'
        cat_items = [x for x in news_list if x.get('category') == cat_name]
        if not cat_items: content_html += f'<div class="empty-msg">Chưa có tin tức.</div>'
        else:
            for item in cat_items: content_html += create_card(item)
        content_html += '</div>\n'

    html_template = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
        <title>KINVEST News Feed Pro</title>
        <style>
            * {{ box-sizing: border-box; }}
            body {{ background-color: #F8FAFC; color: #1F2937; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px 15px; }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            .header {{ background: #FFFFFF; padding: 20px 25px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; border-top: 4px solid #8B5CF6; }}
            .header-left h1 {{ margin: 0; font-size: 22px; color: #111827; font-weight: 800; letter-spacing: -0.5px; }}
            .status {{ color: #6B7280; font-size: 13px; margin-top: 4px; text-align: right; }}
            .live-dot {{ display: inline-block; width: 8px; height: 8px; background-color: #10B981; border-radius: 50%; margin-right: 5px; animation: pulse 2s infinite; }}
            .tabs-wrapper {{ overflow-x: auto; white-space: nowrap; margin-bottom: 20px; border-bottom: 2px solid #E5E7EB; padding-bottom: 5px; scrollbar-width: none; }}
            .tabs-wrapper::-webkit-scrollbar {{ display: none; }}
            .tab-btn {{ background: none; border: none; padding: 8px 16px; font-size: 14px; font-weight: 600; color: #6B7280; cursor: pointer; border-radius: 20px; transition: all 0.2s; display: inline-block; margin-right: 5px; }}
            .tab-btn:hover {{ color: #8B5CF6; background: #F5F3FF; }}
            .tab-btn.active {{ color: #FFFFFF; background: #8B5CF6; box-shadow: 0 2px 4px rgba(139,92,246,0.3); }}
            .tab-content {{ display: none; animation: fadeIn 0.3s ease; }}
            .tab-content.active {{ display: block; }}
            @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(5px); }} to {{ opacity: 1; transform: translateY(0); }} }}
            .news-card {{ background: #FFFFFF; padding: 18px 24px; border-radius: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); margin-bottom: 12px; border-left: 4px solid transparent; transition: all 0.2s ease; }}
            .news-card:hover {{ border-left: 4px solid #8B5CF6; box-shadow: 0 4px 6px rgba(0,0,0,0.08); transform: translateX(2px); }}
            .news-title {{ margin: 0 0 10px 0; font-size: 16px; line-height: 1.5; }}
            .news-title a {{ color: #1F2937; text-decoration: none; font-weight: 600; }}
            .news-title a:hover {{ color: #8B5CF6; }}
            .news-meta {{ font-size: 12px; color: #9CA3AF; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
            .category-badge {{ font-weight: 700; background: #F3F4F6; color: #4B5563; padding: 4px 8px; border-radius: 6px; }}
            .sentiment-badge {{ font-weight: 700; padding: 4px 8px; border-radius: 6px; font-size: 11px; }}
            .empty-msg {{ text-align: center; color: #6B7280; padding: 40px; font-style: italic; background: #FFFFFF; border-radius: 10px; }}
            @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} 100% {{ opacity: 1; }} }}
        </style>
        <meta http-equiv="refresh" content="180">
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="header-left"><h1>KINVEST RADAR PRO</h1></div>
                <div class="header-right">
                    <div class="status"><span class="live-dot"></span>Hệ thống Đa Nguồn & NLP</div>
                    <div class="status" style="font-size: 12px; margin-top: 6px;">Cập nhật: <b>{now_str}</b></div>
                </div>
            </div>
            <div class="tabs-wrapper">{tabs_html}</div>
            <div id="news-container">{content_html}</div>
        </div>
        <script>
            function openTab(evt, tabId) {{
                var i, tabcontent, tablinks;
                tabcontent = document.getElementsByClassName("tab-content");
                for (i = 0; i < tabcontent.length; i++) tabcontent[i].classList.remove("active");
                tablinks = document.getElementsByClassName("tab-btn");
                for (i = 0; i < tablinks.length; i++) tablinks[i].classList.remove("active");
                document.getElementById(tabId).classList.add("active");
                evt.currentTarget.classList.add("active");
            }}
        </script>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as file:
        file.write(html_template)

if __name__ == "__main__":
    print("Khởi động Lõi NLP và càn quét đa nguồn...")
    db = fetch_and_update_db()
    generate_html(db)
    print("Hoàn tất!")
