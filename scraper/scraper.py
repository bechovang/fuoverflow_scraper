# scraper/scraper.py

import os
import re
import json
import time
import requests
from typing import Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm
import config # Import cấu hình từ config.py
from scraper.media_api import extract_media_ids_from_thread, get_media_data_from_json_api
from scraper.pdf_generator import create_pdf_from_data

def sanitize_filename(name: str) -> str:
    """Làm sạch tên file/thư mục để loại bỏ các ký tự không hợp lệ."""
    # Xóa các tiền tố không cần thiết để tên thư mục gọn hơn
    name = re.sub(r'^\s*Đề Thi [A-Z]+\s*-\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'^[a-zA-Z0-9]+\s*-\s*', '', name, flags=re.IGNORECASE)
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()

def make_relative_path(absolute_path: str, base_dir: str = config.SAVE_DIRECTORY) -> Optional[str]:
    """
    Convert absolute path thành relative path từ base_dir.
    
    Args:
        absolute_path: Đường dẫn tuyệt đối
        base_dir: Thư mục base (mặc định: SAVE_DIRECTORY)
    
    Returns:
        Đường dẫn tương đối (với / thay vì \), hoặc None nếu absolute_path là None
    """
    if not absolute_path:
        return None
    
    abs_path = os.path.abspath(absolute_path)
    abs_base = os.path.abspath(base_dir)
    
    try:
        # Lấy relative path
        rel_path = os.path.relpath(abs_path, abs_base)
        # Normalize: convert \ thành / (để tương thích cross-platform)
        rel_path = rel_path.replace('\\', '/')
        return rel_path
    except ValueError:
        # Nếu không cùng drive (Windows), return absolute path
        return absolute_path

def get_absolute_path(relative_path: str, base_dir: str = config.SAVE_DIRECTORY) -> Optional[str]:
    """
    Convert relative path thành absolute path.
    
    Args:
        relative_path: Đường dẫn tương đối
        base_dir: Thư mục base (mặc định: SAVE_DIRECTORY)
    
    Returns:
        Đường dẫn tuyệt đối, hoặc None nếu relative_path là None
    """
    if not relative_path:
        return None
    
    abs_base = os.path.abspath(base_dir)
    abs_path = os.path.join(abs_base, relative_path)
    return os.path.normpath(abs_path)

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

def download_images_with_comments_from_thread(
    session: requests.Session, 
    thread_info: dict,
    thread_db_id: Optional[int] = None
) -> dict:
    """
    Tải tất cả hình ảnh và comments từ một URL đề thi sử dụng JSON API.
    Lưu ảnh và comments vào thư mục riêng, đồng thời tạo file JSON.
    
    Args:
        session: requests.Session với cookies
        thread_info: Dict chứa 'url' và 'title'
        thread_db_id: ID của thread trong DB (optional, để tích hợp sau)
    
    Returns:
        dict chứa:
            - folder_path: Đường dẫn thư mục (relative)
            - pdf_path: Đường dẫn file PDF (relative, None nếu không có)
            - total_questions: Tổng số câu hỏi
            - media_items_data: List các dict chứa thông tin media items
            - success: bool
            - error: str (nếu có lỗi)
    """
    thread_url = thread_info['url']
    folder_name = sanitize_filename(thread_info['title'])
    thread_save_path = os.path.join(config.SAVE_DIRECTORY, folder_name)
    os.makedirs(thread_save_path, exist_ok=True)
    
    print(f"\n--- Đang xử lý đề: '{thread_info['title']}' ---")
    print(f"    Lưu tại: {thread_save_path}")

    result = {
        'folder_path': None,
        'pdf_path': None,
        'total_questions': 0,
        'media_items_data': [],
        'success': False,
        'error': None
    }

    try:
        # Bước 1: Trích xuất Media IDs và CSRF token từ thread
        print("    [*] Đang trích xuất Media IDs và CSRF token...")
        media_items, csrf_token = extract_media_ids_from_thread(session, thread_url)
        
        if not media_items:
            error_msg = "Không tìm thấy media nào trong đề thi này."
            print(f"    -> {error_msg}")
            result['error'] = error_msg
            return result
        
        if not csrf_token:
            print("    (!) Cảnh báo: Không lấy được CSRF token. Có thể gặp lỗi 400 khi gọi API.")
            print("    (!) Vui lòng kiểm tra lại cookie hoặc cập nhật cookie mới nhất.")
        else:
            print(f"    [+] Đã lấy CSRF token thành công.")
        
        print(f"    [+] Tìm thấy {len(media_items)} media items. Bắt đầu tải...")
        
        # Danh sách để lưu dữ liệu cho PDF
        all_question_data = []
        
        # Load dữ liệu cũ từ comments.json nếu có (để tái sử dụng cho file đã tồn tại)
        old_data_dict = {}
        json_save_path = os.path.join(thread_save_path, 'comments.json')
        if os.path.exists(json_save_path):
            try:
                with open(json_save_path, 'r', encoding='utf-8') as f:
                    old_data_list = json.load(f)
                    for item in old_data_list:
                        if 'media_id' in item:
                            old_data_dict[str(item['media_id'])] = item
            except Exception:
                pass  # Nếu không load được thì bỏ qua
        
        # Bước 2: Duyệt qua từng media item và lấy dữ liệu qua JSON API
        for idx, media_item in enumerate(tqdm(media_items, desc="    Xử lý", unit="item", leave=False)):
            media_id = media_item['media_id']
            original_filename = media_item['filename']
            
            # Tạo tên file để kiểm tra
            file_ext = os.path.splitext(original_filename)[1] or '.jpg'
            safe_filename = sanitize_filename(original_filename) or f"question_{idx+1}{file_ext}"
            save_path = os.path.join(thread_save_path, safe_filename)
                
            # Kiểm tra file đã tồn tại chưa - Nếu có thì skip luôn, không gọi API
            if os.path.exists(save_path):
                tqdm.write(f"    - Bỏ qua (đã tồn tại): {safe_filename}")
                # Vẫn thêm vào danh sách để tạo PDF (dùng dữ liệu từ file cũ nếu có)
                if str(media_id) in old_data_dict:
                    # Dùng dữ liệu cũ từ comments.json
                    old_item = old_data_dict[str(media_id)]
                    question_data = {
                        'media_id': media_id,
                        'title': old_item.get('title', f'Question {idx+1}'),
                        'image_url': old_item.get('image_url'),
                        'image_local_path': save_path,
                        'comments': old_item.get('comments', [])
                    }
                else:
                    # Không có dữ liệu cũ, dùng dữ liệu mặc định
                    question_data = {
                        'media_id': media_id,
                        'title': f'Question {idx+1}',
                        'image_url': None,
                        'image_local_path': save_path,
                        'comments': []
                    }
                all_question_data.append(question_data)
                continue  # Skip luôn, không gọi API
            
            # File chưa tồn tại, gọi API để lấy dữ liệu
            media_data = get_media_data_from_json_api(session, media_id, csrf_token)
            
            if not media_data:
                tqdm.write(f"    - Bỏ qua media ID {media_id}: Không lấy được dữ liệu")
                time.sleep(config.DELAY_BETWEEN_REQUESTS)
                continue

            # Tải ảnh về
            image_url = media_data.get('image_url')
            if image_url:
                try:
                    download_headers = session.headers.copy()
                    download_headers['Referer'] = thread_url
                    img_response = session.get(image_url, headers=download_headers, timeout=20, stream=True)
                    img_response.raise_for_status()
                    
                    with open(save_path, 'wb') as f:
                        for chunk in img_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    tqdm.write(f"    - Đã tải: {safe_filename}")
                    
                except Exception as e:
                    tqdm.write(f"    - Lỗi khi tải ảnh media ID {media_id}: {e}")
                    save_path = None
            
            # Lưu dữ liệu cho PDF và JSON
            question_data = {
                'media_id': media_id,
                'title': media_data.get('title', f'Question {idx+1}'),
                'image_url': image_url,
                'image_local_path': save_path if image_url else None,
                'comments': media_data.get('comments', [])
            }
            all_question_data.append(question_data)
            
            # Nghỉ giữa các request
            time.sleep(config.DELAY_BETWEEN_REQUESTS)
        
        # Bước 3: Lưu tất cả comments vào file JSON
        json_save_path = os.path.join(thread_save_path, 'comments.json')
        with open(json_save_path, 'w', encoding='utf-8') as f:
            json.dump(all_question_data, f, ensure_ascii=False, indent=2)
        print(f"    [+] Đã lưu comments vào: comments.json")
        
        # Bước 4: Tạo PDF tự động sau khi cào xong
        pdf_path = None
        if config.GENERATE_PDF:
            if all_question_data:
                pdf_path = os.path.join(thread_save_path, f"{folder_name}.pdf")
                print(f"\n    [*] Đang tạo file PDF...")
                try:
                    create_pdf_from_data(session, all_question_data, pdf_path, thread_info['title'])
                    print(f"    [+] Đã tạo PDF thành công: {os.path.basename(pdf_path)}")
                except Exception as e:
                    print(f"    (!) Lỗi khi tạo PDF: {e}")
                    print(f"    (!) Bạn vẫn có thể tạo PDF sau bằng file comments.json")
                    pdf_path = None  # Set None nếu lỗi
            else:
                print(f"    (!) Không có dữ liệu để tạo PDF. Kiểm tra lại quá trình cào dữ liệu.")
        else:
            print(f"    [*] PDF generation đã được tắt trong config (GENERATE_PDF = False)")
        
        # Chuẩn bị data để return và lưu DB
        media_items_data = []
        for idx, q_data in enumerate(all_question_data):
            media_items_data.append({
                'media_id': q_data['media_id'],
                'filename': os.path.basename(q_data['image_local_path']) if q_data.get('image_local_path') else None,
                'image_path': make_relative_path(q_data.get('image_local_path')) if q_data.get('image_local_path') else None,
                'image_url': q_data.get('image_url'),
                'title': q_data.get('title'),
                'comments': q_data.get('comments', []),
                'question_order': idx + 1
            })
        
        # Convert paths sang relative
        result.update({
            'folder_path': make_relative_path(thread_save_path),
            'pdf_path': make_relative_path(pdf_path) if pdf_path else None,
            'total_questions': len(all_question_data),
            'media_items_data': media_items_data,
            'success': True
        })
        
        print(f"\n    -> Hoàn tất. Đã xử lý {len(all_question_data)}/{len(media_items)} media items.")
        return result

    except requests.exceptions.RequestException as e:
        error_msg = f"Lỗi khi truy cập vào đề thi {thread_url}: {e}"
        print(f"(!) {error_msg}")
        result['error'] = error_msg
        return result
    except Exception as e:
        error_msg = f"Lỗi không xác định: {e}"
        print(f"(!) {error_msg}")
        result['error'] = error_msg
        return result

def main():
    """Hàm chính điều khiển toàn bộ quá trình."""
    print("--- BẮT ĐẦU CHƯƠNG TRÌNH CÀO ẢNH & COMMENTS FUOVERFLOW ---")
    if not config.COOKIES:
        print("(!) Lỗi: Cookie chưa được cấu hình trong file 'config.py'. Vui lòng kiểm tra lại.")
        return
    
    session = requests.Session()
    session.cookies.update(config.COOKIES)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    os.makedirs(config.SAVE_DIRECTORY, exist_ok=True)
    
    # Kiểm tra xem FORUM_URL là thread cụ thể hay forum page
    if '/threads/' in config.FORUM_URL:
        # Là thread cụ thể, xử lý trực tiếp
        thread_info = {
            'url': config.FORUM_URL,
            'title': os.path.basename(config.FORUM_URL.rstrip('/'))
        }
        download_images_with_comments_from_thread(session, thread_info)
    else:
        # Là forum page, lấy danh sách threads
        latest_threads = get_latest_thread_info(session, limit=getattr(config, 'THREAD_LIMIT', 10))
    
    if not latest_threads:
        print("\n(!) Không thể lấy danh sách đề thi. Chương trình kết thúc.")
        return
        
        print(f"\n[*] Sẽ tiến hành cào ảnh và comments từ {len(latest_threads)} đề thi mới nhất.")
    
    for thread_info in latest_threads:
            download_images_with_comments_from_thread(session, thread_info)
        
    print("\n--- HOÀN TẤT TOÀN BỘ QUÁ TRÌNH ---")
    print(f"Tất cả ảnh và comments đã được lưu trong thư mục: '{os.path.abspath(config.SAVE_DIRECTORY)}'")

if __name__ == "__main__":
    main()