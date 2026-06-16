import requests
from bs4 import BeautifulSoup
import datetime
import os

# Đã bổ sung các từ khóa phổ biến để test (Thị trường, Cổ phiếu, VN-Index)
KEYWORDS = ['DIG', 'CEO', 'NTL', 'DXG', 'CTD', 'SSI', 'Trái phiếu', 'Phát hành', 'Lợi nhuận', 'Thị trường', 'Cổ phiếu', 'VN-Index']

RSS_URLS = [
    'https://cafef.vn/tin-tuc-chung-khoan.rss',
    'https://cafef.vn/bat-dong-san.rss'
]

def fetch_news():
    news_list = []
    seen_links = set()
    
    for url in RSS_URLS:
        try:
            # Nâng cấp User-Agent để ngụy trang thành trình duyệt Chrome thật, tránh bị Firewall chặn
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            }
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, features="xml")
            items = soup.findAll('item')
            
            for item in items:
                title = item.title.text if item.title else ""
                link = item.link.text if item.link else ""
                pub_date = item.pubDate.text if item.pubDate else ""
                description = item.description.text if item.description else ""
                
                if link in seen_links:
                    continue
                
                for keyword in KEYWORDS:
                    if keyword.lower() in title.lower() or keyword.lower() in description.lower():
                        news_list.append({
                            "keyword": keyword.upper(),
                            "title": title,
                            "time": pub_date,
                            "link": link
                        })
                        seen_links.add(link)
                        break
        except Exception as e:
            print(f"Lỗi: {e}")
            
    return news_list[:50]

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
        <title>KINVEST News Terminal</title>
        <style>
            body {{ background-color: #0B0E11; color: #FFFFFF; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #2A2E39; padding-bottom: 10px; margin-bottom: 20px; }}
            h1 {{ margin: 0; color: #00DC64; font-size: 24px; }}
            .status {{ color: #8B94A3; font-size: 14px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ text-align: left; padding: 12px 15px; border-bottom: 1px solid #2A2E39; }}
            th {{ color: #8B94A3; font-weight: bold; font-size: 14px; text-transform: uppercase; background-color: #12161C; }}
            tr:hover {{ background-color: #1E2632; }}
            .badge {{ background-color: rgba(171, 71, 188, 0.2); color: #AB47BC; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; display: inline-block; text-align: center; }}
            a {{ color: #2996FF; text-decoration: none; font-weight: bold; font-size: 15px; line-height: 1.4; }}
            a:hover {{ text-decoration: underline; }}
            .time {{ color: #8B94A3; font-size: 12px; margin-top: 4px; display: block; }}
        </style>
        <meta http-equiv="refresh" content="180">
    </head>
    <body>
        <div class="header">
            <h1>⚡ KINVEST NEWS RADAR</h1>
            <div class="status">Cập nhật lần cuối: <span style="color:#00DC64">{now_str}</span> (Auto-run via GitHub Actions)</div>
        </div>
        <table>
            <thead>
                <tr>
                    <th width="12%">MỤC TIÊU</th>
                    <th width="88%">NỘI DUNG TÓM TẮT</th>
                </tr>
            </thead>
            <tbody>
    """
    
    if not news_list:
        html_content += """<tr><td colspan="2" style="text-align:center; color:#8B94A3; padding: 30px;">Chưa có tin tức mới khớp với bộ lọc.</td></tr>"""
    else:
        for item in news_list:
            html_content += f"""
                <tr>
                    <td><span class="badge">{item['keyword']}</span></td>
                    <td><a href="{item['link']}" target="_blank">{item['title']}</a><span class="time">Đăng lúc: {item['time']}</span></td>
                </tr>
            """
            
    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as file:
        file.write(html_content)

if __name__ == "__main__":
    print("Bắt đầu lấy dữ liệu và tạo Web...")
    news = fetch_news()
    generate_html(news)
    print("Đã tạo xong index.html!")
