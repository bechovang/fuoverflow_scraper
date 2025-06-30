# scraper/scraper.py

import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse
from tqdm import tqdm
import config  # Import cấu hình từ config.py

def scrape_images_from_fuoverflow():
    """
    Hàm chính để cào và tải ảnh từ URL được cấu hình trong config.py.
    """
    # Lấy thông tin từ file config
    page_url = config.TARGET_URL
    cookies = config.COOKIES
    save_dir = config.SAVE_DIRECTORY
    
    if not cookies:
        print("Lỗi: Chuỗi cookie chưa được cấu hình hoặc không hợp lệ trong file 'config.py'.")
        print("Vui lòng làm theo hướng dẫn trong file config.py để thêm cookie.")
        return

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    print(f"Đang truy cập trang: {page_url}")
    
    try:
        response = requests.get(page_url, headers=headers, cookies=cookies)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        image_links = soup.select('ul.attachmentList a.file-preview.js-lbImage')

        if not image_links:
            print("Không tìm thấy link ảnh nào. Vui lòng kiểm tra lại:")
            print("- URL trong config.py có đúng không.")
            print("- Cookie đăng nhập còn hợp lệ không.")
            return

        print(f"Tìm thấy {len(image_links)} ảnh. Bắt đầu tải về thư mục '{save_dir}'...")

        # --- THAY ĐỔI CHÍNH BẮT ĐẦU TỪ ĐÂY ---
        # Sử dụng enumerate để có được chỉ số (index) cho mỗi ảnh, bắt đầu từ 1
        for index, link in enumerate(tqdm(image_links, desc="Đang tải ảnh", unit="ảnh"), start=1):
            relative_url = link.get('href')
            
            if not relative_url or not isinstance(relative_url, str):
                continue

            full_image_url = urljoin(page_url, relative_url)

            try:
                # 1. Lấy tên file gốc chỉ để xác định phần mở rộng (.jpg, .png, etc.)
                original_filename = ""
                filename_span = link.find('span', class_='file-name')
                if filename_span:
                    original_filename = filename_span.text.strip()
                else:
                    original_filename = os.path.basename(urlparse(relative_url).path)

                # 2. Tách lấy phần mở rộng của file
                if original_filename:
                    _, extension = os.path.splitext(original_filename)
                    # Nếu file không có phần mở rộng (ví dụ: 'imagefile'), mặc định là .jpg
                    if not extension:
                        extension = ".jpg"
                else:
                    # Nếu không thể lấy tên file, mặc định là .jpg
                    extension = ".jpg"

                # 3. Tạo tên file mới theo định dạng "số_thứ_tự.phần_mở_rộng"
                new_filename = f"{index}{extension}"
                
                # 4. Tạo đường dẫn đầy đủ để lưu file
                save_path = os.path.join(save_dir, new_filename)
                
                # Bỏ qua nếu file đã tồn tại để tránh tải lại
                if os.path.exists(save_path):
                    # tqdm.write sẽ in ra màn hình mà không làm hỏng thanh tiến trình
                    tqdm.write(f"Bỏ qua: File '{new_filename}' đã tồn tại.")
                    continue

                # Tải nội dung ảnh
                img_response = requests.get(full_image_url, headers=headers, cookies=cookies, stream=True)
                img_response.raise_for_status()

                # Lưu file với tên mới
                with open(save_path, 'wb') as f:
                    for chunk in img_response.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            except requests.exceptions.RequestException as e:
                tqdm.write(f"\nLỗi khi tải ảnh {full_image_url}: {e}")
        # --- KẾT THÚC THAY ĐỔI ---

        print(f"\nHoàn tất! Tất cả ảnh đã được kiểm tra và tải về thành công.")

    except requests.exceptions.RequestException as e:
        print(f"\nLỗi nghiêm trọng khi truy cập URL {page_url}: {e}")
        print("Hãy chắc chắn rằng bạn đã kết nối internet và cookie là chính xác.")

if __name__ == "__main__":
    scrape_images_from_fuoverflow()