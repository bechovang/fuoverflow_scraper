# FuOverflow Exam Scraper v1.0

Dự án này là một script Python tự động tải về ảnh đề thi, comments/đáp án và tạo file PDF từ các thread trên diễn đàn FuOverflow Community.

**Version:** 1.0  
**Last Updated:** 2025  
**Status:** ✅ Stable

## ✨ Tính năng v1.0

### Core Features
- ✅ **Tải ảnh đề thi**: Tải về ảnh gốc chất lượng cao, không phải thumbnail
- ✅ **Trích xuất comments/đáp án**: Tự động lấy tất cả bình luận từ mỗi câu hỏi
- ✅ **JSON API Integration**: Sử dụng JSON API chính thức của XenForo để lấy dữ liệu chính xác
- ✅ **CSRF Token Support**: Tự động xử lý CSRF token để tránh lỗi 400 Bad Request
- ✅ **Tự động tạo PDF**: Tạo file PDF với format chuyên nghiệp
  - Trang lẻ (1, 3, 5...): Hiển thị câu hỏi (ảnh đề thi)
  - Trang chẵn (2, 4, 6...): Hiển thị đáp án và bình luận

### Performance & UX
- ✅ **Smart Skip**: Tự động bỏ qua file đã tồn tại, không gọi API không cần thiết
- ✅ **Progress Bar**: Hiển thị thanh tiến trình với tqdm
- ✅ **Error Handling**: Xử lý lỗi tốt, thông báo rõ ràng
- ✅ **Unicode Font Support**: Tự động tải font Unicode để hiển thị tiếng Việt trong PDF

### Security & Reliability
- ✅ **Cookie-based Authentication**: Xác thực qua cookie từ trình duyệt
- ✅ **Rate Limiting**: Tự động nghỉ giữa các request để tránh bị ban
- ✅ **Retry Logic**: Xử lý lỗi và retry khi cần

## Hướng dẫn cài đặt và sử dụng

### 1. Yêu cầu hệ thống

- **Python**: 3.7 trở lên
- **OS**: Windows, macOS, hoặc Linux
- **Dependencies**: Xem `requirements.txt`

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

**Lưu ý:** Script sẽ tự động:
- Tạo thư mục `downloaded_images` nếu chưa có
- Bỏ qua file đã tồn tại (không tải lại)
- Tự động tạo PDF sau khi cào xong (nếu `GENERATE_PDF = True`)

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
    ├── question_1.jpg          # Ảnh câu hỏi 1
    ├── question_2.jpg          # Ảnh câu hỏi 2
    ├── ...
    ├── comments.json            # Tất cả comments/đáp án (JSON format)
    └── [Tên đề thi].pdf         # File PDF tổng hợp
```

## 🔧 Troubleshooting

### Lỗi thường gặp

#### 1. Lỗi 400 Bad Request
**Nguyên nhân:** CSRF token hết hạn hoặc cookie không hợp lệ  
**Giải pháp:**
- Cập nhật cookie mới nhất trong `config.py`
- Đảm bảo `xf_session` và `xf_user` trong cookie còn hiệu lực
- Script sẽ tự động lấy CSRF token, nhưng cần cookie hợp lệ

#### 2. Lỗi font PDF (Character outside range)
**Nguyên nhân:** Font không hỗ trợ tiếng Việt  
**Giải pháp:**
- Script sẽ tự động tải font DejaVu nếu cần
- Hoặc đặt `PDF_FONT_PATH` trong `config.py` trỏ đến font Unicode (ví dụ: `C:\Windows\Fonts\arialuni.ttf`)

#### 3. Không tìm thấy media items
**Nguyên nhân:** URL sai hoặc cookie không có quyền truy cập  
**Giải pháp:**
- Kiểm tra lại `FORUM_URL` trong `config.py`
- Đảm bảo bạn đã đăng nhập và có quyền xem thread đó
- Kiểm tra cookie có đầy đủ không

#### 4. Script chạy chậm
**Nguyên nhân:** Nhiều request, delay giữa các request  
**Giải pháp:**
- Giảm `DELAY_BETWEEN_REQUESTS` trong `config.py` (nhưng không nên < 1 giây)
- File đã tồn tại sẽ được skip nhanh, không cần lo

## 📝 Maintenance

### Cập nhật cookie định kỳ
Cookie có thể hết hạn sau một thời gian. Nên cập nhật cookie mới nhất trong `config.py` mỗi khi:
- Gặp lỗi 400 Bad Request
- Script không thể truy cập thread
- Cookie đã cũ (thường sau vài ngày/tuần)

### Cấu trúc code
```
fuoverflow_scraper/
├── config.py              # Cấu hình (URL, cookie, settings)
├── main.py                # Script cũ (có thể bỏ qua)
├── scraper/
│   ├── __init__.py
│   ├── scraper.py         # Main scraper logic
│   ├── media_api.py       # JSON API handler & CSRF token
│   └── pdf_generator.py   # PDF generation với Unicode support
├── requirements.txt       # Dependencies
└── README.md             # Tài liệu này
```

### Dependencies
- `requests`: HTTP requests
- `beautifulsoup4`: HTML parsing
- `tqdm`: Progress bar
- `fpdf2`: PDF generation
- `Pillow`: Image processing

### Cập nhật dependencies
```bash
pip install --upgrade -r requirements.txt
```

## ⚠️ Disclaimer

Script này được tạo ra cho mục đích:
- ✅ Học tập và nghiên cứu
- ✅ Sao lưu dữ liệu cá nhân
- ✅ Tạo tài liệu ôn thi offline

**Vui lòng:**
- ❌ Không sử dụng để spam hoặc tải quá nhiều dữ liệu
- ❌ Không chia sẻ cookie với người khác
- ❌ Tôn trọng điều khoản dịch vụ của FuOverflow
- ❌ Không sử dụng cho mục đích thương mại không được phép

## 📄 License

Dự án này chỉ dành cho mục đích giáo dục và cá nhân.

## 🤝 Contributing

Nếu bạn muốn đóng góp:
1. Fork repository
2. Tạo branch mới cho feature
3. Commit changes
4. Tạo Pull Request

## 📧 Support

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra phần Troubleshooting ở trên
2. Kiểm tra cookie và URL trong `config.py`
3. Xem log để tìm lỗi cụ thể

---

**Version 1.0** - Stable Release  
*Last updated: 2025*