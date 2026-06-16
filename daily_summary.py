import json
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta, timezone
import os

DB_FILE = 'news_database.json'

def generate_daily_summary():
    vn_tz = timezone(timedelta(hours=7))
    now_vn = datetime.now(vn_tz)
    today_date = now_vn.date()
    
    # 1. Rút data trực tiếp từ kho, không cần quét mạng
    if not os.path.exists(DB_FILE):
        news_list = []
    else:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            db_news = json.load(f)
            
        news_list = []
        for item in db_news:
            try:
                # Đọc giờ trong kho và ép về múi giờ VN
                dt = parsedate_to_datetime(item['time'] + " +0700")
                dt_vn = dt.astimezone(vn_tz)
                
                # BỘ LỌC THỜI GIAN: Chỉ nhặt tin Hôm nay + Khung giờ 6h đến 19h
                if dt_vn.date() == today_date and 6 <= dt_vn.hour < 19:
                    news_list.append({
                        "title": item['title'],
                        "time": dt_vn.strftime("%H:%M"),
                        "link": item['link'],
                        "dt_obj": dt_vn
                    })
            except Exception:
                continue
                
    # Xếp tin từ mới nhất đến cũ nhất
    news_list.sort(key=lambda x: x["dt_obj"], reverse=True)

    # 2. Xây dựng Giao diện (Giữ nguyên y hệt bản cũ)
    now_str = now_vn.strftime("%d/%m/%Y")
    
    html = f"""<!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
        <title>Bản tin tổng hợp cuối ngày - {now_str}</title>
        <style>
            body {{ background-color: #F8FAFC; color: #1F2937; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 40px 20px; line-height: 1.6; }}
            .container {{ max-width: 800px; margin: 0 auto; background: #FFFFFF; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 6px solid #10B981; }}
            .header {{ text-align: center; border-bottom: 2px solid #E5E7EB; padding-bottom: 20px; margin-bottom: 30px; }}
            h1 {{ color: #111827; font-size: 28px; margin: 0 0 10px 0; text-transform: uppercase; letter-spacing: -0.5px; }}
            .date {{ color: #6B7280; font-size: 15px; font-weight: 600; display: inline-block; background: #F3F4F6; padding: 6px 16px; border-radius: 20px; }}
            .intro {{ font-size: 16px; color: #4B5563; font-style: italic; margin-bottom: 30px; text-align: center; }}
            .news-item {{ padding: 16px 0; border-bottom: 1px dashed #E5E7EB; display: flex; gap: 15px; align-items: baseline; transition: transform 0.2s; }}
            .news-item:hover {{ transform: translateX(5px); }}
            .news-item:last-child {{ border-bottom: none; }}
            .time-badge {{ background: #EFF6FF; color: #2563EB; padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: 700; white-space: nowrap; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }}
            .title {{ font-size: 16px; margin: 0; }}
            .title a {{ color: #1F2937; text-decoration: none; font-weight: 600; transition: color 0.2s; }}
            .title a:hover {{ color: #10B981; }}
            .footer {{ margin-top: 40px; text-align: center; font-size: 13px; color: #9CA3AF; padding-top: 20px; border-top: 1px solid #E5E7EB; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>BẢN TIN THỊ TRƯỜNG CUỐI NGÀY</h1>
                <div class="date">Ngày {now_str} (Từ 06:00 - 19:00)</div>
            </div>
            <div class="intro">Toàn cảnh các sự kiện và tin tức kinh tế - chứng khoán đáng chú ý nhất trong phiên giao dịch.</div>
    """
    
    if not news_list:
        html += "<div style='text-align:center; color:#9CA3AF; padding:40px;'>Không có tin tức nào được ghi nhận trong khung giờ này.</div>"
    else:
        for item in news_list:
            html += f"""
            <div class="news-item">
                <div class="time-badge">{item['time']}</div>
                <h3 class="title"><a href="{item['link']}" target="_blank">{item['title']}</a></h3>
            </div>
            """
            
    html += """
            <div class="footer">Tự động tổng hợp bởi KINVEST News Radar qua hệ thống GitHub Actions.</div>
        </div>
    </body>
    </html>
    """
    
    with open("tong-hop-ngay.html", "w", encoding="utf-8") as file:
        file.write(html)

if __name__ == "__main__":
    generate_daily_summary()
