import requests
from bs4 import BeautifulSoup
import datetime
import json
import os
from email.utils import parsedate_to_datetime

# Ánh xạ trực tiếp 12 chuyên mục gốc (đọc thẳng từ giao diện Web, bỏ qua RSS)
SOURCES = {
    "Chứng khoán": "https://cafef.vn/thi-truong-chung-khoan.chn",
    "Bất động sản": "https://cafef.vn/bat-dong-san.chn",
    "Xã hội": "https://cafef.vn/xa-hoi.chn",
    "Doanh nghiệp": "https://cafef.vn/doanh-nghiep.chn",
    "Ngân hàng": "https://cafef.vn/tai-chinh-ngan-hang.chn",
    "Smart Money": "https://cafef.vn/smart-money.chn",
    "Quốc tế": "https://cafef.vn/tai-chinh-quoc-te.chn",
    "Vĩ mô": "https://cafef.vn/vi-mo-dau-tu.chn",
    "Kinh tế số": "https://cafef.vn/kinh-te-so.chn",
    "Sống": "https://cafef.vn/song.chn",
    "Thị trường": "https://cafef.vn/thi-truong.chn",
    "Lifestyle": "https://cafef.vn/lifestyle.chn"
}

DB_FILE = 'news_database.json'

def fetch_and_update_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try:
                db_news = json.load(f)
            except:
                db_news = []
    else:
        db_news = []

    # Dùng hàm .get() để chống sập nếu gặp data cũ thiếu trường
    seen_links = {item.get('link', '') for item in db_news}
    new_articles = []
    
    # Lấy giờ hiện tại làm mốc cho các tin cào được (Giờ VN)
    utc_now = datetime.datetime.utcnow()
    vn_time = utc_now + datetime.timedelta(hours=7)
    
    # Định dạng giờ giả lập chuẩn RSS để Bot "Tổng hợp cuối ngày" không bị sập
    fake_rss_time = vn_time.strftime("%a, %d %b %Y %H:%M:%S")
    current_ts = vn_time.timestamp()

    for cat_name, url in SOURCES.items():
        try:
            # Ngụy trang thành trình duyệt Chrome thật
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36'}
            response = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Cào trực tiếp mọi thẻ <a> trên trang web
            links = soup.find_all('a')
            count = 0
            
            for a in links:
                if count >= 15: # Chỉ nhặt 15 tin mới nhất ở trên cùng mỗi trang
                    break
                    
                href = a.get('href', '')
                title = a.get('title', '').strip()
                if not title:
                    title = a.text.strip()
                    
                # Lọc lấy bài báo chuẩn (chỉ lấy link chứa đuôi .chn, loại bỏ link rác)
                if href.endswith('.chn') and len(title) > 20:
                    if href.startswith('/'):
                        href = 'https://cafef.vn' + href
                        
                    if href not in seen_links:
                        new_articles.append({
                            "category": cat_name,
                            "title": title,
                            "time": fake_rss_time,
                            "timestamp": current_ts,
                            "link": href
                        })
                        seen_links.add(href)
                        count += 1
                        current_ts -= 1 # Lùi nhẹ mốc thời gian để giữ đúng thứ tự hiển thị
                        
        except Exception as e:
            print(f"Lỗi quét HTML {cat_name}: {e}")

    updated_db = new_articles + db_news
    updated_db.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    updated_db = updated_db[:800] # Nới rộng kho chứa cho dữ liệu khổng lồ
    
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(updated_db, f, ensure_ascii=False, indent=4)
        
    return updated_db

def generate_html(news_list):
    utc_now = datetime.datetime.utcnow()
    vn_time = utc_now + datetime.timedelta(hours=7)
    now_str = vn_time.strftime("%d/%m/%Y %H:%M:%S")
    
    tabs_html = f'<button class="tab-btn active" onclick="openTab(event, \'tab_ALL\')">Tất cả tin tức</button>\n'
    for idx, cat_name in enumerate(SOURCES.keys()):
        tabs_html += f'<button class="tab-btn" onclick="openTab(event, \'tab_{idx}\')">{cat_name}</button>\n'

    def create_card(item):
        cat = item.get('category', 'Chung')
        title = item.get('title', 'Không có tiêu đề')
        link = item.get('link', '#')
        
        # Rút gọn giờ hiển thị cho đẹp
        raw_time = item.get('time', '')
        parts = raw_time.split(' ')
        if len(parts) >= 5:
            display_time = f"{parts[4][:5]} ({parts[1]}/{parts[2]})"
        else:
            display_time = raw_time
            
        return f"""
            <div class="news-card">
                <h2 class="news-title"><a href="{link}" target="_blank">{title}</a></h2>
                <div class="news-meta">
                    <span class="category-badge">{cat}</span>
                    <span>🕒 {display_time}</span>
                </div>
            </div>
        """

    content_html = f'<div id="tab_ALL" class="tab-content active">\n'
    if not news_list:
         content_html += '<div class="empty-msg">Chưa tải được dữ liệu, hệ thống đang quét...</div>'
    for item in news_list[:150]: 
        content_html += create_card(item)
    content_html += '</div>\n'

    for idx, cat_name in enumerate(SOURCES.keys()):
        content_html += f'<div id="tab_{idx}" class="tab-content">\n'
        cat_items = [x for x in news_list if x.get('category') == cat_name]
        
        if not cat_items:
            content_html += f'<div class="empty-msg">Chưa có tin tức mới trong mục {cat_name}.</div>'
        else:
            for item in cat_items:
                content_html += create_card(item)
        content_html += '</div>\n'

    html_template = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
        <title>KINVEST News Feed</title>
        <style>
            * {{ box-sizing: border-box; }}
            body {{ background-color: #F8FAFC; color: #1F2937; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 20px 15px; }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            .header {{ background: #FFFFFF; padding: 20px 25px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; border-top: 4px solid #2563EB; }}
            .header-left h1 {{ margin: 0; font-size: 22px; color: #111827; font-weight: 800; letter-spacing: -0.5px; }}
            .header-right {{ text-align: right; }}
            .status {{ color: #6B7280; font-size: 13px; margin-top: 4px; }}
            .live-dot {{ display: inline-block; width: 8px; height: 8px; background-color: #10B981; border-radius: 50%; margin-right: 5px; animation: pulse 2s infinite; }}
            .tabs-wrapper {{ overflow-x: auto; white-space: nowrap; margin-bottom: 20px; border-bottom: 2px solid #E5E7EB; padding-bottom: 5px; scrollbar-width: none; }}
            .tabs-wrapper::-webkit-scrollbar {{ display: none; }}
            .tab-btn {{ background: none; border: none; padding: 10px 18px; font-size: 15px; font-weight: 600; color: #6B7280; cursor: pointer; border-radius: 20px; transition: all 0.2s; display: inline-block; }}
            .tab-btn:hover {{ color: #2563EB; background: #EFF6FF; }}
            .tab-btn.active {{ color: #FFFFFF; background: #2563EB; box-shadow: 0 2px 4px rgba(37,99,235,0.3); }}
            .tab-content {{ display: none; animation: fadeIn 0.3s ease; }}
            .tab-content.active {{ display: block; }}
            @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(5px); }} to {{ opacity: 1; transform: translateY(0); }} }}
            .news-card {{ background: #FFFFFF; padding: 18px 24px; border-radius: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); margin-bottom: 12px; border-left: 3px solid transparent; transition: all 0.2s ease; }}
            .news-card:hover {{ border-left: 3px solid #2563EB; box-shadow: 0 4px 6px rgba(0,0,0,0.08); transform: translateX(2px); }}
            .news-title {{ margin: 0 0 8px 0; font-size: 16px; line-height: 1.5; }}
            .news-title a {{ color: #1F2937; text-decoration: none; font-weight: 600; }}
            .news-title a:hover {{ color: #2563EB; }}
            .news-meta {{ font-size: 13px; color: #9CA3AF; display: flex; align-items: center; gap: 15px; }}
            .category-badge {{ font-size: 11px; font-weight: 700; background: #EEF2FF; color: #2563EB; padding: 4px 10px; border-radius: 6px; text-transform: uppercase; }}
            .empty-msg {{ text-align: center; color: #6B7280; padding: 40px; font-style: italic; background: #FFFFFF; border-radius: 10px; }}
            @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} 100% {{ opacity: 1; }} }}
            @media (max-width: 600px) {{ .header {{ flex-direction: column; align-items: flex-start; gap: 15px; }} .header-right {{ text-align: left; }} }}
        </style>
        <meta http-equiv="refresh" content="180">
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="header-left"><h1>KINVEST NEWS FEED</h1></div>
                <div class="header-right">
                    <div class="status"><span class="live-dot"></span>Hệ thống Radar Live</div>
                    <div class="status" style="font-size: 12px; margin-top: 6px;">Cập nhật: <b>{now_str}</b></div>
                </div>
            </div>
            
            <div class="tabs-wrapper">
                {tabs_html}
            </div>
            
            <div id="news-container">
                {content_html}
            </div>
        </div>

        <script>
            function openTab(evt, tabId) {{
                var i, tabcontent, tablinks;
                tabcontent = document.getElementsByClassName("tab-content");
                for (i = 0; i < tabcontent.length; i++) {{
                    tabcontent[i].classList.remove("active");
                }}
                tablinks = document.getElementsByClassName("tab-btn");
                for (i = 0; i < tablinks.length; i++) {{
                    tablinks[i].classList.remove("active");
                }}
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
    print("Bắt đầu lấy dữ liệu Deep HTML Scraper...")
    db = fetch_and_update_db()
    generate_html(db)
    print("Đã tạo xong index.html!")
