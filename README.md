# FuOverflow Exam Scraper v2.0

Dự án này là một script Python tự động tải về ảnh đề thi, comments/đáp án và tạo file PDF từ các thread trên diễn đàn FuOverflow Community.

**Version:** 2.0 (với Library & Queue System)  
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

### Library & Queue System (v2.0) 🆕
- ✅ **Library Management**: Quản lý thư viện threads với SQLite database
- ✅ **Queue System**: Hàng chờ xử lý threads tự động (FIFO)
- ✅ **Background Worker**: Worker chạy liên tục để xử lý queue
- ✅ **Batch Add**: Thêm nhiều URL cùng lúc vào queue
- ✅ **Status Tracking**: Theo dõi trạng thái (pending, processing, completed, failed)
- ✅ **Database Storage**: Lưu trữ metadata và media items trong database
- ✅ **CLI Interface**: Giao diện dòng lệnh để quản lý library và queue

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

#### Cách 1: Sử dụng Library & Queue System (Khuyến khích - v2.0)

Sau khi cài đặt và cấu hình xong, bạn có thể sử dụng CLI mới:

```bash
# Thêm một URL vào queue
python main.py add https://fuoverflow.com/threads/csi106-fa25-re.5577/

# Thêm nhiều URL cùng lúc
python main.py add url1 url2 url3

# Xem danh sách threads trong library
python main.py list
python main.py list --status pending
python main.py list --status completed --limit 10

# Xem thống kê queue
python main.py stats

# Xem chi tiết một thread
python main.py show <thread_id>

# Retry các thread failed
python main.py retry --all
python main.py retry --id <thread_id>

# Chạy worker để xử lý queue (loop liên tục)
python main.py worker

# Chạy worker (dừng khi queue rỗng)
python main.py worker --stop-on-empty

# Chạy worker với interval tùy chỉnh (mặc định: 5 giây)
python main.py worker --interval 10
```

**Quy trình làm việc:**
1. Thêm URL vào queue: `python main.py add <url>`
2. Chạy worker: `python main.py worker` (trong terminal riêng, chạy liên tục)
3. Worker sẽ tự động xử lý các thread pending theo thứ tự FIFO
4. Kiểm tra status: `python main.py list` hoặc `python main.py stats`

#### Cách 2: Chạy script cũ (v1.0 - vẫn hỗ trợ)

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

#### 5. Database locked error
**Nguyên nhân:** Nhiều process đang truy cập database cùng lúc  
**Giải pháp:**
- Đảm bảo chỉ có 1 worker đang chạy
- Đóng tất cả connections trước khi chạy lại
- Nếu vẫn lỗi, restart terminal/process

#### 6. Worker không xử lý queue
**Nguyên nhân:** Worker đã dừng hoặc gặp lỗi  
**Giải pháp:**
- Kiểm tra worker có đang chạy không
- Chạy lại worker: `python main.py worker`
- Kiểm tra logs để tìm lỗi

## 📝 Maintenance

### Cập nhật cookie định kỳ
Cookie có thể hết hạn sau một thời gian. Nên cập nhật cookie mới nhất trong `config.py` mỗi khi:
- Gặp lỗi 400 Bad Request
- Script không thể truy cập thread
- Cookie đã cũ (thường sau vài ngày/tuần)

### Database Maintenance

#### Backup Database
```bash
# Backup database
cp fuoverflow.db fuoverflow_backup.db
# Hoặc trên Windows:
copy fuoverflow.db fuoverflow_backup.db
```

#### Reset Database
```bash
# Xóa database để reset hoàn toàn
rm fuoverflow.db
# Hoặc trên Windows:
del fuoverflow.db
```

#### Migrate Database (nếu cần)
Database schema có thể thay đổi trong các phiên bản sau. Nếu cần migrate:
1. Backup database hiện tại
2. Xóa database cũ
3. Chạy lại script (database sẽ được tạo lại với schema mới)

#### Query Database (nếu cần)
Bạn có thể sử dụng SQLite command line để query database:

```bash
sqlite3 fuoverflow.db

# Xem tất cả threads
SELECT * FROM threads;

# Xem threads pending
SELECT * FROM threads WHERE status = 'pending';

# Xem threads completed
SELECT * FROM threads WHERE status = 'completed';

# Đếm media items của một thread
SELECT COUNT(*) FROM media_items WHERE thread_id = 1;

# Exit
.quit
```

### Worker Maintenance

#### Chạy Worker liên tục
Worker nên chạy liên tục trong terminal riêng để xử lý queue tự động:

```bash
python main.py worker
```

Worker sẽ:
- Tự động lấy thread pending cũ nhất (FIFO)
- Xử lý thread đó
- Tiếp tục với thread tiếp theo
- Sleep giữa các lần check queue (mặc định 5 giây)

#### Dừng Worker
Nhấn `Ctrl+C` để dừng worker một cách an toàn.

#### Worker với Interval
Nếu muốn giảm tần suất check queue (ví dụ: để tiết kiệm tài nguyên):

```bash
python main.py worker --interval 30  # Check mỗi 30 giây
```

#### Worker Stop on Empty
Nếu chỉ muốn xử lý queue hiện tại rồi dừng:

```bash
python main.py worker --stop-on-empty
```

### Xử lý Threads Failed

#### Xem Threads Failed
```bash
# Xem danh sách threads failed
python main.py list --status failed

# Xem chi tiết một thread failed
python main.py show <thread_id>
```

#### Retry Failed Threads
Nếu có threads bị failed (do lỗi network, cookie hết hạn, v.v.), bạn có thể retry:

```bash
# Retry tất cả failed threads
python main.py retry --all

# Retry một thread cụ thể
python main.py retry --id <thread_id>
```

Sau khi retry, threads sẽ được reset về status `pending` và sẽ được xử lý lại khi worker chạy.

**Lưu ý:**
- Trước khi retry, nên kiểm tra lỗi: `python main.py show <thread_id>` để xem error message
- Nếu lỗi do cookie hết hạn, cần cập nhật cookie trong `config.py` trước khi retry
- Nếu lỗi do URL không hợp lệ hoặc thread không tồn tại, retry sẽ vẫn fail

### File Management

#### Cấu trúc thư mục
```
downloaded_images/
└── [thread_folder]/        # Relative path từ SAVE_DIRECTORY
    ├── question_1.jpg
    ├── question_2.jpg
    ├── ...
    ├── comments.json
    └── [thread_folder].pdf
```

#### Cleanup Files
Nếu muốn xóa files đã tải về:
- Xóa thư mục `downloaded_images/` để xóa tất cả files
- Hoặc xóa từng thư mục cụ thể
- **Lưu ý:** Database vẫn giữ metadata, chỉ xóa files thực tế

#### Disk Space
- Mỗi thread có thể chiếm 10-50MB (tùy số lượng câu hỏi)
- PDF files thường 1-5MB mỗi file
- Database file (`fuoverflow.db`) thường nhỏ (< 1MB)

### Performance Tips

1. **Batch Add URLs:**
   ```bash
   # Thêm nhiều URL cùng lúc thay vì từng URL một
   python main.py add url1 url2 url3 url4 url5
   ```

2. **Worker Interval:**
   - Giảm interval nếu muốn xử lý nhanh hơn: `--interval 2`
   - Tăng interval nếu muốn giảm tải server: `--interval 10`

3. **Rate Limiting:**
   - Giữ `DELAY_BETWEEN_REQUESTS` ở mức 2 giây trở lên
   - Không nên giảm xuống < 1 giây (có thể bị ban)

4. **Concurrent Workers:**
   - Hiện tại chỉ hỗ trợ 1 worker
   - Chạy nhiều worker cùng lúc có thể gây conflict (sẽ hỗ trợ trong tương lai)

### Troubleshooting Database

#### Database locked
Nếu gặp lỗi "database is locked":
- Đảm bảo chỉ có 1 worker đang chạy
- Đóng tất cả connections trước khi chạy lại

#### Database corrupted
Nếu database bị corrupted:
1. Backup database hiện tại (nếu có thể)
2. Xóa database cũ: `rm fuoverflow.db`
3. Chạy lại script (database sẽ được tạo lại)

#### Migration Issues
Nếu gặp lỗi khi update code:
- Backup database
- Xóa database cũ
- Chạy lại script (schema mới sẽ được tạo)

### Cấu trúc code (v2.0)

```
fuoverflow_scraper/
├── config.py              # Cấu hình (URL, cookie, settings)
├── main.py                # CLI entry point (Library & Queue)
├── fuoverflow.db          # SQLite database (tự động tạo)
├── database/              # Database layer
│   ├── __init__.py
│   └── models.py          # Database models & DatabaseManager
├── library/               # Library management
│   ├── __init__.py
│   ├── thread_utils.py    # Extract thread info từ URL
│   └── library_manager.py # Library CRUD operations
├── queue_system/          # Queue management
│   ├── __init__.py
│   ├── queue_manager.py   # Queue operations
│   └── worker.py          # Background worker (Phase 5)
├── scraper/               # Scraper logic
│   ├── __init__.py
│   ├── scraper.py         # Main scraper logic (refactored)
│   ├── media_api.py       # JSON API handler & CSRF token
│   └── pdf_generator.py   # PDF generation với Unicode support
├── requirements.txt       # Dependencies
└── README.md             # Tài liệu này
```

### Database Schema

Hệ thống sử dụng SQLite database với 2 bảng chính:

#### Bảng `threads`
- `id`: Primary key
- `url`: URL của thread (UNIQUE)
- `title`: Tiêu đề thread
- `status`: Trạng thái (pending, processing, completed, failed)
- `folder_path`: Đường dẫn thư mục (relative path)
- `pdf_path`: Đường dẫn file PDF (relative path)
- `total_questions`: Tổng số câu hỏi
- `created_at`, `updated_at`, `completed_at`: Timestamps
- `error_message`: Thông báo lỗi (nếu có)

#### Bảng `media_items`
- `id`: Primary key
- `thread_id`: Foreign key → threads.id
- `media_id`: Media ID từ FUO
- `filename`: Tên file
- `image_path`: Đường dẫn file ảnh (relative path)
- `image_url`: URL gốc từ server
- `title`: Tiêu đề câu hỏi
- `comments_json`: Comments dạng JSON string
- `question_order`: Thứ tự câu hỏi
- `created_at`: Timestamp

**Lưu ý:** Tất cả đường dẫn được lưu dạng relative (tương đối) để dễ di chuyển giữa các máy.

### Dependencies
- `requests`: HTTP requests
- `beautifulsoup4`: HTML parsing
- `tqdm`: Progress bar
- `fpdf2`: PDF generation
- `Pillow`: Image processing
- SQLite3: Built-in Python (không cần cài đặt)

### Cập nhật dependencies
```bash
pip install --upgrade -r requirements.txt
```

## 📚 Library & Queue System (v2.0)

### Tổng quan

Hệ thống Library & Queue cho phép:
- Quản lý nhiều threads trong một database
- Thêm nhiều URL vào queue cùng lúc
- Xử lý tự động với background worker
- Theo dõi trạng thái và lỗi
- Tránh duplicate (không cào lại thread đã có)

### Quy trình làm việc

1. **Thêm threads vào queue:**
   ```bash
   python main.py add https://fuoverflow.com/threads/thread1.123/
   python main.py add url1 url2 url3  # Batch add
   ```

2. **Chạy worker (trong terminal riêng):**
   ```bash
   python main.py worker
   ```
   Worker sẽ:
   - Lấy thread pending cũ nhất (FIFO)
   - Update status = processing
   - Gọi scraper để cào dữ liệu
   - Lưu media items vào database
   - Update status = completed/failed
   - Lặp lại cho thread tiếp theo

3. **Kiểm tra status:**
   ```bash
   python main.py list              # Tất cả threads
   python main.py list --status pending    # Chỉ pending
   python main.py stats             # Thống kê queue
   python main.py show <thread_id>  # Chi tiết một thread
   ```

4. **Xử lý lỗi:**
   ```bash
   # Xem threads failed
   python main.py list --status failed
   
   # Retry tất cả failed threads
   python main.py retry --all
   
   # Retry một thread cụ thể
   python main.py retry --id <thread_id>
   ```

### CLI Commands

#### `add <urls...>`
Thêm một hoặc nhiều URL vào queue.

```bash
python main.py add https://fuoverflow.com/threads/test.123/
python main.py add url1 url2 url3
```

- Nếu URL đã tồn tại: Hiển thị thông tin thread hiện có
- Nếu URL mới: Tạo thread mới với status = pending

#### `list [--status STATUS] [--limit N]`
Liệt kê threads trong library.

```bash
python main.py list
python main.py list --status pending
python main.py list --status completed --limit 10
```

Options:
- `--status`: Lọc theo status (pending, processing, completed, failed)
- `--limit`: Giới hạn số lượng kết quả

#### `worker [--stop-on-empty] [--interval N]`
Chạy background worker để xử lý queue.

```bash
python main.py worker                    # Loop liên tục
python main.py worker --stop-on-empty    # Dừng khi queue rỗng
python main.py worker --interval 10      # Check queue mỗi 10 giây
```

Options:
- `--stop-on-empty`: Dừng worker khi không còn pending threads
- `--interval`: Thời gian nghỉ giữa các lần check queue (giây, mặc định: 5)

#### `stats`
Xem thống kê queue.

```bash
python main.py stats
```

Hiển thị số lượng threads theo từng status.

#### `show <thread_id>`
Xem chi tiết một thread.

```bash
python main.py show 1
```

Hiển thị thông tin chi tiết:
- ID, title, URL, status
- Timestamps (created, updated, completed)
- Folder path và số lượng files
- PDF path và file size
- Total questions
- Error message (nếu có)
- Media items count

#### `retry [--all|--id <thread_id>]`
Retry các thread failed.

```bash
python main.py retry --all              # Retry tất cả failed threads
python main.py retry --id <thread_id>   # Retry một thread cụ thể
```

- Reset status từ `failed` → `pending`
- Xóa error message
- Thread sẽ được xử lý lại khi chạy worker

### Status Flow

```
pending → processing → completed
                      ↓
                     failed
```

- **pending**: Thread mới được thêm vào queue
- **processing**: Worker đang xử lý thread này
- **completed**: Thread đã được xử lý thành công
- **failed**: Thread gặp lỗi khi xử lý

### Database File

Database được lưu trong file `fuoverflow.db` (SQLite) ở thư mục gốc của project.

- **Backup**: Copy file `fuoverflow.db` để backup
- **Reset**: Xóa file `fuoverflow.db` để reset database
- **Di chuyển**: File database có thể di chuyển giữa các máy (paths là relative)

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

## 🏗️ Architecture

### Component Overview

1. **Database Layer** (`database/`):
   - `DatabaseManager`: Quản lý SQLite database
   - Models: `Thread`, `MediaItem`, `ThreadStatus`

2. **Library Layer** (`library/`):
   - `LibraryManager`: CRUD operations cho threads
   - `thread_utils`: Extract thread info từ URL

3. **Queue Layer** (`queue_system/`):
   - `QueueManager`: Quản lý queue operations
   - `QueueWorker`: Background worker để xử lý queue

4. **Scraper Layer** (`scraper/`):
   - `scraper.py`: Main scraping logic (refactored)
   - `media_api.py`: JSON API & CSRF token
   - `pdf_generator.py`: PDF generation

### Data Flow

```
User → CLI (main.py) → LibraryManager → Database
                       ↓
                      QueueManager → Database
                       ↓
                      Worker → Scraper → Files + Database
```

### Path Management

Tất cả paths được lưu dạng **relative** (tương đối) từ `SAVE_DIRECTORY`:
- `folder_path`: `csi106-fa25-re.5577`
- `pdf_path`: `csi106-fa25-re.5577/csi106-fa25-re.5577.pdf`
- `image_path`: `csi106-fa25-re.5577/question_1.jpg`

Điều này giúp:
- Dễ di chuyển project giữa các máy
- Database portable
- Tương thích Windows/Mac/Linux

---

**Version 2.0** - Library & Queue System  
*Last updated: 2025*