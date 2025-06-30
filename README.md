# FuOverflow Image Scraper

Dự án này là một script Python dùng để tự động tải về tất cả các ảnh đính kèm từ một trang thread cụ thể trên diễn đàn FuOverflow Community.

## Tính năng

- Tải về ảnh gốc với chất lượng đầy đủ, không phải ảnh thumbnail.
- Xử lý xác thực (đăng nhập) thông qua việc sử dụng cookie từ trình duyệt.
- Lưu trữ ảnh vào một thư mục được chỉ định.
- Hiển thị thanh tiến trình (progress bar) trong quá trình tải.
- Cấu trúc code sạch sẽ, dễ dàng mở rộng.

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
2.  **Cập nhật `TARGET_URL`**: Dán URL của thread bạn muốn cào.
3.  **Cập nhật `COOKIES`**: Đây là bước quan trọng nhất.
    - Đăng nhập vào `fuoverflow.com` trên trình duyệt.
    - Nhấn **F12** để mở Developer Tools, chọn tab **Network**.
    - Tải lại trang, chọn request đầu tiên (tên trang).
    - Trong phần **Request Headers**, tìm dòng `cookie:` và copy toàn bộ giá trị của nó.
    - Dán chuỗi cookie đó vào biến `COOKIES` trong `config.py`.

### 4. Chạy Script

Sau khi cài đặt và cấu hình xong, chạy script bằng lệnh sau từ thư mục gốc `fuoverflow_scraper`:

```bash
python -m scraper.scraper
```

Ảnh sẽ được tải về thư mục downloaded_images được tạo tự động trong thư mục gốc của dự án.
Disclaimer
Script này được tạo ra cho mục đích học tập và sao lưu dữ liệu cá nhân. Vui lòng tôn trọng điều khoản dịch vụ của trang web FuOverflow và không sử dụng nó cho các mục đích xấu.
Generated code
---

#### **File: `requirements.txt`**

File này giúp người khác có thể cài đặt chính xác các phiên bản thư viện mà bạn đã dùng.