# scraper/scraper.py

import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm
import config # Import cấu hình từ config.py

def sanitize_filename(name: str) -> str:
    """Làm sạch tên file/thư mục để loại bỏ các ký tự không hợp lệ."""
    # Xóa các tiền tố không cần thiết để tên thư mục gọn hơn
    name = re.sub(r'^\s*Đề Thi [A-Z]+\s*-\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'^[a-zA-Z0-9]+\s*-\s*', '', name, flags=re.IGNORECASE)
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()

def get_latest_thread_info(session, limit: int) -> list[dict]:
    """Lấy thông tin (URL và tiêu đề) của các đề thi mới nhất."""
    print(f"[*] Đang truy cập trang môn học: {config.FORUM_URL}")
    try:
        response = session.get(config.FORUM_URL, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        thread_items = soup.select('div.structItem.structItem--thread')
        
        if not thread_items:
            print("(!) Không tìm thấy danh sách đề thi. Kiểm tra lại URL môn học hoặc cookie.")
            return []

        print(f"[+] Tìm thấy {len(thread_items)} đề thi trên trang đầu tiên.")
        
        threads_info = []
        for item in thread_items[:limit]:
            title_tag = item.select_one('div.structItem-title > a[data-tp-primary="on"]')
            if title_tag and title_tag.has_attr('href'):
                threads_info.append({
                    'url': urljoin(config.FORUM_URL, title_tag['href']),
                    'title': title_tag.text.strip()
                })
        
        return threads_info
        
    except requests.exceptions.RequestException as e:
        print(f"(!) Lỗi kết nối đến trang môn học: {e}")
        return []

def download_images_from_thread(session, thread_info: dict):
    """Tải tất cả hình ảnh từ một URL đề thi và lưu vào thư mục riêng."""
    thread_url = thread_info['url']
    folder_name = sanitize_filename(thread_info['title'])
    thread_save_path = os.path.join(config.SAVE_DIRECTORY, folder_name)
    os.makedirs(thread_save_path, exist_ok=True)
    
    print(f"\n--- Đang xử lý đề: '{thread_info['title']}' ---")
    print(f"    Lưu tại: {thread_save_path}")

    try:
        response = session.get(thread_url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        attachment_links = soup.select('ul.attachmentList a.file-preview.js-lbImage')
        
        if not attachment_links:
            print("    -> Không tìm thấy ảnh đính kèm nào trong đề thi này.")
            return

        print(f"    -> Tìm thấy {len(attachment_links)} ảnh đính kèm. Bắt đầu tải...")
        
        download_count = 0
        for link in tqdm(attachment_links, desc="    Tải ảnh", unit="ảnh", leave=False):
            if not link.has_attr('href'):
                continue
            
            direct_image_url = urljoin(thread_url, link['href'])
            
            try:
                filename_span = link.find('span', class_='file-name')
                filename = sanitize_filename(filename_span.text.strip()) if filename_span else "unknown_image.jpg"
                save_path = os.path.join(thread_save_path, filename)
                
                if os.path.exists(save_path):
                    continue

                # **SỬA LỖI QUAN TRỌNG: Thêm 'Referer' header**
                # Header này báo cho server biết ta đang truy cập từ trang đề thi
                download_headers = session.headers.copy()
                download_headers['Referer'] = thread_url
                
                img_data_response = session.get(direct_image_url, timeout=20, stream=True, headers=download_headers)
                img_data_response.raise_for_status()
                
                with open(save_path, 'wb') as f:
                    for chunk in img_data_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                download_count += 1
            
            except requests.exceptions.RequestException as e:
                tqdm.write(f"\n    - Lỗi khi tải ảnh {direct_image_url}: {e}")
        
        print(f"    -> Hoàn tất. Đã tải mới {download_count}/{len(attachment_links)} ảnh.")

    except requests.exceptions.RequestException as e:
        print(f"(!) Lỗi khi truy cập vào đề thi {thread_url}: {e}")

def main():
    """Hàm chính điều khiển toàn bộ quá trình."""
    print("--- BẮT ĐẦU CHƯƠNG TRÌNH CÀO ẢNH FUOVERFLOW ---")
    if not config.COOKIES:
        print("(!) Lỗi: Cookie chưa được cấu hình trong file 'config.py'. Vui lòng kiểm tra lại.")
        return
    
    session = requests.Session()
    session.cookies.update(config.COOKIES)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    os.makedirs(config.SAVE_DIRECTORY, exist_ok=True)
    
    latest_threads = get_latest_thread_info(session, limit=config.THREAD_LIMIT)
    
    if not latest_threads:
        print("\n(!) Không thể lấy danh sách đề thi. Chương trình kết thúc.")
        return
        
    print(f"\n[*] Sẽ tiến hành cào ảnh từ {len(latest_threads)} đề thi mới nhất.")
    
    for thread_info in latest_threads:
        download_images_from_thread(session, thread_info)
        
    print("\n--- HOÀN TẤT TOÀN BỘ QUÁ TRÌNH ---")
    print(f"Tất cả ảnh đã được lưu trong thư mục: '{os.path.abspath(config.SAVE_DIRECTORY)}'")

if __name__ == "__main__":
    main()