import requests
from bs4 import BeautifulSoup
import datetime

# Không cần bộ lọc từ khóa nữa
# Bổ sung thêm chuyên mục Vĩ mô để có cái nhìn toàn cảnh
RSS_URLS = [
    'https://cafef.vn/tin-tuc-chung-khoan.rss',
    'https://cafef.vn/bat-dong-san.rss',
    'https://cafef.vn/vi-mo-dau-tu.rss'
]

def fetch_news():
    news_list = []
    seen_links = set()
    
    for url in RSS_URLS:
        try:
            # Ngụy trang User-Agent chuẩn
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
                'Accept': 'application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8'
            }
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, features="xml")
            items = soup.findAll('item')
            
            # Lấy 25 tin mới nhất từ mỗi chuyên mục để gộp lại
            for item in items[:25]:
                title = item.title.text if item.title else ""
                link = item.link.text if item.link else ""
                pub_date = item.pubDate.text if item.pubDate else ""
                
                # Cắt bỏ múi giờ thừa cho đẹp (+0700)
                pub_date = pub_date.replace("+0700", "").strip()
                
                if link not in seen_links and link != "":
                    news_list.append({
                        "title": title,
                        "time": pub_date,
                        "link": link
                    })
                    seen_links.add(link)
        except Exception as e:
            print(f"Lỗi quét {url}: {e}")
            
    return news_list[:75] # Hiển thị tổng cộng 75 tin mới nhất

def generate_html(news_list):
    # Ép múi giờ về GMT+7 (Việt Nam)
    utc_now = datetime.datetime.utcnow()
    vn_time = utc_now + datetime.timedelta(hours=7)
    now_str = vn_time.strftime("%d/%m/%Y %H:%M:%S")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        
        <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
        <meta http-equiv="Pragma" content="no-cache" />
        <meta http-equiv="Expires" content="0" />
        
        <title>KINVEST News Feed</title>
        <style>
            /* Reset & Base */
            * {{ box-sizing: border-box; }}
            body {{
                background-color: #F3F4F6; /* Nền xám rất sáng, dịu mắt */
                color: #1F2937; /* Chữ xám đen, giảm chói so với đen tuyền */
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 30px 15px;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
            }}
            
            /* Header */
            .header {{
                background: #FFFFFF;
                padding: 24px 30px;
                border-radius: 12px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                margin-bottom: 25px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-top: 4px solid #2563EB; /* Viền xanh dương điểm xuyết */
            }}
            .header-left h1 {{
                margin: 0;
                font-size: 22px;
                color: #111827;
                font-weight: 800;
                letter-spacing: -0.5px;
            }}
            .header-right {{
                text-align: right;
            }}
            .status {{
                color: #6B7280;
                font-size: 13px;
                margin-top: 4px;
            }}
            .live-dot {{
                display: inline-block;
                width: 8px; height: 8px;
                background-color: #10B981;
                border-radius: 50%;
                margin-right: 5px;
                animation: pulse 2s infinite;
            }}
            
            /* News Cards */
            .news-feed {{
                display: flex;
                flex-direction: column;
                gap: 12px;
            }}
            .news-card {{
                background: #FFFFFF;
                padding: 18px 24px;
                border-radius: 10px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.04);
                border-left: 3px solid transparent;
                transition: all 0.2s ease;
            }}
            .news-card:hover {{
                border-left: 3px solid #2563EB;
                box-shadow: 0 4px 6px rgba(0,0,0,0.08);
                transform: translateX(2px);
            }}
            .news-title {{
                margin: 0 0 8px 0;
                font-size: 16px;
                line-height: 1.5;
            }}
            .news-title a {{
                color: #1F2937;
                text-decoration: none;
                font-weight: 600;
            }}
            .news-title a:hover {{
                color: #2563EB; /* Đổi màu xanh khi hover */
            }}
            .news-meta {{
                font-size: 13px;
                color: #9CA3AF;
                display: flex;
                align-items: center;
                gap: 15px;
            }}
            
            /* Animation */
            @keyframes pulse {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.4; }}
                100% {{ opacity: 1; }}
            }}
            
            /* Responsive */
            @media (max-width: 600px) {{
                .header {{ flex-direction: column; align-items: flex-start; gap: 15px; }}
                .header-right {{ text-align: left; }}
            }}
        </style>
        <meta http-equiv="refresh" content="180">
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="header-left">
                    <h1>KINVEST NEWS FEED</h1>
                </div>
                <div class="header-right">
                    <div class="status"><span class="live-dot"></span>Hệ thống Radar Live</div>
                    <div class="status" style="font-size: 12px; margin-top: 6px;">Cập nhật: <b>{now_str}</b></div>
                </div>
            </div>
            
            <div class="news-feed">
    """
    
    if not news_list:
        html_content += """
            <div class="news-card" style="text-align: center; color: #6B7280; padding: 40px;">
                Chưa thể tải dữ liệu tin tức. Đang quét lại...
            </div>
        """
    else:
        for item in news_list:
            html_content += f"""
                <div class="news-card">
                    <h2 class="news-title">
                        <a href="{item['link']}" target="_blank">{item['title']}</a>
                    </h2>
                    <div class="news-meta">
                        <span>🕒 {item['time']}</span>
                        <span>• Nguồn: CafeF</span>
                    </div>
                </div>
            """
            
    html_content += """
            </div>
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as file:
        file.write(html_content)

if __name__ == "__main__":
    print("Bắt đầu lấy dữ liệu toàn bộ thị trường...")
    news = fetch_news()
    generate_html(news)
    print("Đã tạo xong index.html!")
