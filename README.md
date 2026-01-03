# FuOverflow Image Scraper

Dự án này là một script Python dùng để tự động tải về tất cả các ảnh đính kèm từ một trang thread cụ thể trên diễn đàn FuOverflow Community.

## Tính năng

- ✅ Tải về ảnh gốc với chất lượng đầy đủ, không phải ảnh thumbnail.
- ✅ **MỚI**: Tự động trích xuất và lưu comments/đáp án từ mỗi câu hỏi.
- ✅ **MỚI**: Sử dụng JSON API để lấy dữ liệu chính xác và nhanh hơn.
- ✅ **MỚI**: Tự động tạo file PDF với format: trang lẻ = câu hỏi, trang chẵn = đáp án.
- ✅ Xử lý xác thực (đăng nhập) thông qua việc sử dụng cookie từ trình duyệt.
- ✅ Lưu trữ ảnh và comments vào thư mục được chỉ định.
- ✅ Hiển thị thanh tiến trình (progress bar) trong quá trình tải.
- ✅ Cấu trúc code sạch sẽ, dễ dàng mở rộng.

## Hướng dẫn cài đặt và sử dụng

### 1. Chuẩn bị

- Đã cài đặt Python 3.7+ trên máy.

### 2. Cài đặt

1.  **Clone repository này về máy:**
    ```bash
    git clone <URL-cua-repo-nay>
    cd fuoverflow_scraper
    ```

2.  **Tạo và kích hoạt môi trường ảo (khuyến khích):**
    ```bash
    # Trên Windows
    python -m venv venv
    .\venv\Scripts\activate

    # Trên macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Cài đặt các thư viện cần thiết:**
    ```bash
    pip install -r requirements.txt
    ```

### 3. Cấu hình

Trước khi chạy, bạn cần cung cấp thông tin đăng nhập (cookie) và URL mục tiêu.

1.  Mở file `config.py`.
2.  **Cập nhật `FORUM_URL`**: Dán URL của thread cụ thể bạn muốn cào (ví dụ: `https://fuoverflow.com/threads/csi106-fa25-re.5577/`) hoặc URL của forum page.
3.  **Cập nhật `RAW_COOKIE_STRING`**: Đây là bước quan trọng nhất.
    - Đăng nhập vào `fuoverflow.com` trên trình duyệt.
    - Nhấn **F12** để mở Developer Tools, chọn tab **Network**.
    - Tải lại trang, chọn request đầu tiên (tên trang).
    - Trong phần **Request Headers**, tìm dòng `cookie:` và copy toàn bộ giá trị của nó.
    - Dán chuỗi cookie đó vào biến `RAW_COOKIE_STRING` trong `config.py`.
4.  **Cấu hình tùy chọn** (không bắt buộc):
    - `GENERATE_PDF = True/False`: Bật/tắt tạo file PDF (mặc định: True)
    - `PDF_FONT_PATH`: Đường dẫn đến file font .ttf nếu muốn hiển thị tiếng Việt tốt hơn (mặc định: None)
    - `DELAY_BETWEEN_REQUESTS`: Thời gian nghỉ giữa các request (giây) để tránh bị ban (mặc định: 2)
    - `MAX_COMMENTS_PER_QUESTION`: Số lượng comment tối đa hiển thị trong PDF (mặc định: 5)

### 4. Chạy Script

Sau khi cài đặt và cấu hình xong, chạy script bằng lệnh sau từ thư mục gốc `fuoverflow_scraper`:

```bash
python -m scraper.scraper
```

## Kết quả

Sau khi chạy script, bạn sẽ có:

- **Ảnh đề thi**: Được lưu trong `downloaded_images/[Tên đề thi]/`
- **File `comments.json`**: Chứa tất cả comments/đáp án kèm metadata cho mỗi câu hỏi
- **File PDF** (nếu `GENERATE_PDF = True`): 
  - Trang lẻ (1, 3, 5...): Hiển thị câu hỏi (ảnh đề thi)
  - Trang chẵn (2, 4, 6...): Hiển thị đáp án và bình luận

### Cấu trúc thư mục sau khi chạy:
```
downloaded_images/
└── [Tên đề thi]/
    ├── question_1.jpg
    ├── question_2.jpg
    ├── ...
    ├── comments.json
    └── [Tên đề thi].pdf
```
Disclaimer
Script này được tạo ra cho mục đích học tập và sao lưu dữ liệu cá nhân. Vui lòng tôn trọng điều khoản dịch vụ của trang web FuOverflow và không sử dụng nó cho các mục đích xấu.
Generated code
---

#### **File: `requirements.txt`**

File này giúp người khác có thể cài đặt chính xác các phiên bản thư viện mà bạn đã dùng.