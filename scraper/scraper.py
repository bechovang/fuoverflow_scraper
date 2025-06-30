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
    
    # Kiểm tra xem người dùng đã nhập cookie chưa
    if not cookies:
        print("Lỗi: Chuỗi cookie chưa được cấu hình trong file 'config.py'.")
        print("Vui lòng làm theo hướng dẫn trong file config.py để thêm cookie.")
        return

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Tạo thư mục lưu ảnh nếu chưa có
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    print(f"Đang truy cập trang: {page_url}")
    
    try:
        # Gửi request với cookie và header
        response = requests.get(page_url, headers=headers, cookies=cookies)
        response.raise_for_status() # Báo lỗi nếu request thất bại (vd: 403, 404, 500)

        soup = BeautifulSoup(response.text, 'html.parser')

        # Selector chính xác để lấy link chứa ảnh gốc
        image_links = soup.select('ul.attachmentList a.file-preview.js-lbImage')

        if not image_links:
            print("Không tìm thấy link ảnh nào. Vui lòng kiểm tra lại:")
            print("- URL trong config.py có đúng không.")
            print("- Cookie đăng nhập còn hợp lệ không.")
            return

        print(f"Tìm thấy {len(image_links)} ảnh. Bắt đầu tải về thư mục '{save_dir}'...")

        # Dùng tqdm để tạo thanh tiến trình
        for link in tqdm(image_links, desc="Đang tải ảnh", unit="ảnh"):
            relative_url = link.get('href')
            if not relative_url:
                continue

            # Nối với domain để tạo URL tuyệt đối
            full_image_url = urljoin(page_url, relative_url)

            try:
                # Lấy tên file từ thẻ span bên trong
                filename_span = link.find('span', class_='file-name')
                if filename_span:
                    filename = filename_span.text.strip()
                else:
                    # Phương án dự phòng nếu không tìm thấy span
                    filename = os.path.basename(urlparse(relative_url).path)

                save_path = os.path.join(save_dir, filename)
                
                # Bỏ qua nếu file đã tồn tại
                if os.path.exists(save_path):
                    continue

                # Tải nội dung ảnh
                img_response = requests.get(full_image_url, headers=headers, cookies=cookies, stream=True)
                img_response.raise_for_status()

                # Lưu file
                with open(save_path, 'wb') as f:
                    for chunk in img_response.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            except requests.exceptions.RequestException as e:
                tqdm.write(f"\nLỗi khi tải ảnh {full_image_url}: {e}") # Dùng tqdm.write để không làm hỏng progress bar

        print(f"\nHoàn tất! Tất cả ảnh đã được kiểm tra và tải về thành công.")

    except requests.exceptions.RequestException as e:
        print(f"\nLỗi nghiêm trọng khi truy cập URL {page_url}: {e}")
        print("Hãy chắc chắn rằng bạn đã kết nối internet và cookie là chính xác.")

# Đoạn này cho phép chạy file trực tiếp bằng lệnh `python -m scraper.scraper`
if __name__ == "__main__":
    scrape_images_from_fuoverflow()