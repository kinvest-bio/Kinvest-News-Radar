import requests
from bs4 import BeautifulSoup
import datetime
import os

# Từ khóa mục tiêu để radar quét
KEYWORDS = ['DIG', 'CEO', 'NTL', 'DXG', 'CTD', 'SSI', 'Trái phiếu', 'Phát hành', 'Lợi nhuận']

RSS_URLS = [
    'https://cafef.vn/tin-tuc-chung-khoan.rss',
    'https://cafef.vn/bat-dong-san.rss'
]

def fetch_news():
    news_list = []
    seen_links = set()
    
    for url in RSS_URLS:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, features="xml")
            items = soup.findAll('item')
            
            for item in items:
                title = item.title.text
                link = item.link.text
                pub_date = item.pubDate.text
                description = item.description.text
                
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
            
    return news_list[:50] # Chỉ giữ 50 tin mới nhất

def generate_html(news_list):
    now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
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
            .badge {{ background-color: rgba(171, 71, 188, 0.2); color: #AB47BC; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }}
            a {{ color: #2996FF; text-decoration: none; font-weight: bold; }}
            a:hover {{ text-decoration: underline; }}
            .time {{ color: #8B94A3; font-size: 13px; }}
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
                    <th width="10%">MỤC TIÊU</th>
                    <th width="90%">NỘI DUNG TÓM TẮT</th>
                </tr>
            </thead>
            <tbody>
    """
    
    if not news_list:
        html_content += """<tr><td colspan="2" style="text-align:center; color:#8B94A3;">Chưa có tin tức mới khớp với bộ lọc.</td></tr>"""
    else:
        for item in news_list:
            html_content += f"""
                <tr>
                    <td><span class="badge">{item['keyword']}</span></td>
                    <td><a href="{item['link']}" target="_blank">{item['title']}</a> <br><span class="time">Đăng lúc: {item['time']}</span></td>
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
