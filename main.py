import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
import re

# --- PHẦN CẤU HÌNH ---

# URL của trang danh sách các bài đăng môn học
FORUM_URL = "https://fuoverflow.com/forums/OSG202/"

# >>> Dán chuỗi cookie mới nhất của bạn vào đây <<<
RAW_COOKIE_STRING = '_ga=GA1.1.54290854.1750900384; _fbp=fb.1.1750900383781.603511674403904435; cf_clearance=NsYHOQyhNCK3T3uI2KZeTWJdtl1YBadm_iZWz83MaZo-1753805314-1.2.1.1-GfKKnOCQSQydi72q.nJxo6eSs6H30gIMkSoBMYsA_A7cWNxW5JiVP712Fpi.qfJkl32p4RdP8h7D.15eGMvekB8FdJ9vTvDaRgxqqSSunvK4C.7VQmSg3k7yYVeV0qfDyxjhYUUbZgn7FrzmdXv0iT_Qi8vXFZseJBkDT5IcJgAc_jkP2bJIDEFgTcaEOPL3GNhMBzhGrfaZbPzSWG4tp.eUJpFFdlxDxuQLcOMJPvM; xf_csrf=ZV-8ewxEKbRT56z8; xf_user=32502%2CD3T_XhE4EPv9FOx4LDstA22-XbEvMUm2GhCbffa1; xf_session=L1pv6lEePtaZtKWlLkf4X6aow4EuqRiO; xf_siropu_chat_channel=room; xf_siropu_chat_room_id=1; _ga_HZ6B4EZ2PR=GS2.1.s1759122020$o15$g1$t1759123166$j56$l0$h0'

# Thư mục chính để lưu tất cả ảnh tải về
SAVE_DIRECTORY = "downloaded_images"

# Số lượng đề thi mới nhất muốn tải
THREAD_LIMIT = 10

# --- PHẦN MÃ NGUỒN (KHÔNG CẦN SỬA) ---

def parse_cookies(cookie_string: str) -> dict[str, str]:
    """Chuyển đổi chuỗi cookie thô thành một dictionary."""
    cookies = {}
    if not cookie_string or 'DÁN-CHUỖI-COOKIE' in cookie_string:
        print("(!) Lỗi: Chuỗi cookie trống. Vui lòng cập nhật biến RAW_COOKIE_STRING.")
        return cookies
    
    for item in cookie_string.split(';'):
        item = item.strip()
        if not item:
            continue
        try:
            key, value = item.split('=', 1)
            cookies[key] = value
        except ValueError:
            pass
    return cookies

def sanitize_filename(name: str) -> str:
    """Làm sạch tên file/thư mục để loại bỏ các ký tự không hợp lệ."""
    # Loại bỏ tiền tố và các phần không cần thiết
    name = re.sub(r'^osg202\s*-\s*', '', name, flags=re.IGNORECASE)
    # Thay thế các ký tự không hợp lệ bằng dấu gạch dưới
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()

def get_latest_thread_info(forum_url: str, cookies: dict, limit: int) -> list[dict]:
    """Lấy thông tin (URL và tiêu đề) của các đề thi mới nhất."""
    print(f"[*] Đang truy cập trang môn học: {forum_url}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        response = requests.get(forum_url, cookies=cookies, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        thread_items = soup.select('div.structItem.structItem--thread')
        
        if not thread_items:
            print("(!) Không tìm thấy danh sách đề thi. Có thể cookie đã hết hạn hoặc cấu trúc trang đã thay đổi.")
            return []

        print(f"[+] Tìm thấy {len(thread_items)} đề thi trên trang đầu tiên.")
        
        threads_info = []
        for item in thread_items[:limit]:
            title_tag = item.select_one('div.structItem-title > a[data-tp-primary="on"]')
            if title_tag and title_tag.has_attr('href'):
                relative_url = title_tag['href']
                absolute_url = urljoin(forum_url, relative_url)
                title = title_tag.text.strip()
                threads_info.append({'url': absolute_url, 'title': title})
        
        return threads_info
        
    except requests.exceptions.RequestException as e:
        print(f"(!) Lỗi kết nối đến trang môn học: {e}")
        return []

def download_images_from_thread(thread_info: dict, cookies: dict, base_save_dir: str):
    """Tải tất cả hình ảnh từ một URL đề thi và lưu vào thư mục riêng."""
    thread_url = thread_info['url']
    thread_title = thread_info['title']
    
    # Tạo thư mục con dựa trên tiêu đề của đề thi
    folder_name = sanitize_filename(thread_title)
    thread_save_path = os.path.join(base_save_dir, folder_name)
    os.makedirs(thread_save_path, exist_ok=True)
    
    print(f"\n--- Đang xử lý đề: '{thread_title}' ---")
    print(f"    Lưu tại: {thread_save_path}")

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        response = requests.get(thread_url, cookies=cookies, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        # Selector này tìm tất cả ảnh trong nội dung bài viết chính
        image_tags = soup.select('div.bbWrapper img')
        
        if not image_tags:
            print("    -> Không tìm thấy ảnh nào trong đề thi này.")
            return

        print(f"    -> Tìm thấy {len(image_tags)} ảnh. Bắt đầu tải...")
        downloaded_count = 0
        for i, img_tag in enumerate(image_tags):
            if not img_tag.has_attr('src'):
                continue

            img_url = urljoin(thread_url, img_tag['src'])
            
            try:
                # Lấy tên file gốc từ URL, giải mã các ký tự đặc biệt (ví dụ: %20 -> space)
                file_name = sanitize_filename(unquote(os.path.basename(img_url.split('?')[0])))
                if not file_name:
                    file_name = f"image_{i+1}.jpg"

                save_path = os.path.join(thread_save_path, file_name)

                # Kiểm tra xem file đã tồn tại chưa để tránh tải lại
                if os.path.exists(save_path):
                    print(f"    - Bỏ qua (đã tồn tại): {file_name}")
                    continue

                img_response = requests.get(img_url, cookies=cookies, headers=headers, timeout=20)
                img_response.raise_for_status()

                if img_response.content:
                    with open(save_path, 'wb') as handler:
                        handler.write(img_response.content)
                    print(f"    - Tải thành công: {file_name}")
                    downloaded_count += 1
                else:
                    print(f"    - Lỗi: Nội dung ảnh rỗng từ {img_url}")

            except requests.exceptions.RequestException as e:
                print(f"    - Lỗi khi tải ảnh {img_url}: {e}")
        
        print(f"    -> Hoàn tất. Đã tải mới {downloaded_count} ảnh.")

    except requests.exceptions.RequestException as e:
        print(f"(!) Lỗi khi truy cập vào đề thi {thread_url}: {e}")

def main():
    """Hàm chính điều khiển toàn bộ quá trình."""
    print("--- BẮT ĐẦU CHƯƠNG TRÌNH CÀO ẢNH FUOVERFLOW ---")
    COOKIES = parse_cookies(RAW_COOKIE_STRING)
    if not COOKIES:
        return
        
    os.makedirs(SAVE_DIRECTORY, exist_ok=True)
    
    latest_threads = get_latest_thread_info(FORUM_URL, COOKIES, limit=THREAD_LIMIT)
    
    if not latest_threads:
        print("\n(!) Không thể lấy danh sách đề thi. Chương trình kết thúc.")
        return
        
    print(f"\n[*] Sẽ tiến hành cào ảnh từ {len(latest_threads)} đề thi mới nhất.")
    
    for thread_info in latest_threads:
        download_images_from_thread(thread_info, COOKIES, SAVE_DIRECTORY)
        
    print("\n--- HOÀN TẤT TOÀN BỘ QUÁ TRÌNH ---")
    print(f"Tất cả ảnh đã được lưu trong thư mục: '{os.path.abspath(SAVE_DIRECTORY)}'")

if __name__ == "__main__":
    main()