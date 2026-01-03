# scraper/pdf_generator.py

import os
import json
import requests
from fpdf import FPDF
from PIL import Image
from typing import List, Dict
import config


def setup_unicode_font(pdf: FPDF):
    """
    Thiết lập font Unicode để hỗ trợ tiếng Việt.
    Ưu tiên: Font từ config > DejaVu (có sẵn) > Font mặc định.
    """
    font_loaded = False
    
    # Phương pháp 1: Sử dụng font từ config nếu có
    if config.PDF_FONT_PATH and os.path.exists(config.PDF_FONT_PATH):
        try:
            pdf.add_font('Unicode', '', config.PDF_FONT_PATH, uni=True)
            pdf.add_font('Unicode', 'B', config.PDF_FONT_PATH, uni=True)
            pdf.add_font('Unicode', 'I', config.PDF_FONT_PATH, uni=True)
            font_loaded = True
        except Exception:
            pass
    
    # Phương pháp 2: Sử dụng DejaVu fonts (có sẵn trong fpdf2)
    if not font_loaded:
        try:
            # Thử tải DejaVu từ thư mục fonts của fpdf2
            from pathlib import Path
            import sys
            
            # Tìm thư mục fonts của fpdf2
            fpdf_path = Path(sys.modules['fpdf'].__file__).parent
            fonts_dir = fpdf_path / 'fonts'
            
            # Thử các font DejaVu
            dejavu_fonts = [
                fonts_dir / 'DejaVuSans.ttf',
                fonts_dir / 'DejaVuSansCondensed.ttf',
            ]
            
            for font_path in dejavu_fonts:
                if font_path.exists():
                    try:
                        pdf.add_font('Unicode', '', str(font_path), uni=True)
                        pdf.add_font('Unicode', 'B', str(font_path), uni=True)
                        pdf.add_font('Unicode', 'I', str(font_path), uni=True)
                        font_loaded = True
                        break
                    except Exception:
                        continue
            
            # Nếu không tìm thấy trong package, thử tải từ internet hoặc dùng font Windows
            if not font_loaded:
                # Thử tìm font trong Windows
                windows_fonts = [
                    r"C:\Windows\Fonts\arial.ttf",
                    r"C:\Windows\Fonts\arialuni.ttf",  # Arial Unicode MS - hỗ trợ tiếng Việt tốt
                    r"C:\Windows\Fonts\tahoma.ttf",
                ]
                
                for font_path in windows_fonts:
                    if os.path.exists(font_path):
                        try:
                            pdf.add_font('Unicode', '', font_path, uni=True)
                            pdf.add_font('Unicode', 'B', font_path, uni=True)
                            pdf.add_font('Unicode', 'I', font_path, uni=True)
                            font_loaded = True
                            break
                        except Exception:
                            continue
                
                # Nếu không tìm thấy font Windows, thử tải DejaVu từ internet
                if not font_loaded:
                    try:
                        dejavu_url = "https://github.com/reingart/pyfpdf/raw/master/fpdf/font/DejaVuSans.ttf"
                        local_font_path = "DejaVuSans.ttf"
                        
                        if not os.path.exists(local_font_path):
                            print("    [*] Đang tải font DejaVu để hỗ trợ tiếng Việt...")
                            response = requests.get(dejavu_url, timeout=30)
                            if response.status_code == 200:
                                with open(local_font_path, 'wb') as f:
                                    f.write(response.content)
                                print("    [+] Đã tải font DejaVu thành công.")
                        
                        if os.path.exists(local_font_path):
                            pdf.add_font('Unicode', '', local_font_path, uni=True)
                            pdf.add_font('Unicode', 'B', local_font_path, uni=True)
                            pdf.add_font('Unicode', 'I', local_font_path, uni=True)
                            font_loaded = True
                    except Exception as e:
                        pass
        except Exception:
            pass
    
    return font_loaded


class ExamPDF(FPDF):
    """Class tùy chỉnh cho PDF đề thi."""
    
    def __init__(self):
        super().__init__()
        self.unicode_font_available = setup_unicode_font(self)
        if not self.unicode_font_available:
            print("    [!] Cảnh báo: Không thể tải font Unicode. PDF có thể không hiển thị đúng tiếng Việt.")
    
    def header(self):
        """Header cho mỗi trang."""
        font_name = 'Unicode' if self.unicode_font_available else 'Arial'
        self.set_font(font_name, 'I', 8)
        self.cell(0, 10, 'Tài liệu ôn thi FuOverflow', 0, 0, 'C')
    
    def footer(self):
        """Footer cho mỗi trang."""
        font_name = 'Unicode' if self.unicode_font_available else 'Arial'
        self.set_y(-15)
        self.set_font(font_name, 'I', 8)
        self.cell(0, 10, f'Trang {self.page_no()}', 0, 0, 'C')


def download_image_for_pdf(session: requests.Session, img_url: str, temp_path: str) -> bool:
    """Tải ảnh về thư mục tạm để chèn vào PDF."""
    try:
        headers = session.headers.copy()
        headers['Referer'] = config.FORUM_URL
        response = session.get(img_url, headers=headers, timeout=20, stream=True)
        response.raise_for_status()
        
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"    (!) Lỗi khi tải ảnh cho PDF: {e}")
        return False


def create_pdf_from_data(session: requests.Session, data_list: List[Dict], output_path: str, thread_title: str):
    """
    Tạo file PDF từ danh sách dữ liệu câu hỏi.
    
    Args:
        session: requests.Session để tải ảnh
        data_list: List các dict chứa image_url, comments, title
        output_path: Đường dẫn file PDF đầu ra
        thread_title: Tiêu đề đề thi
    """
    pdf = ExamPDF()
    
    # Sử dụng font Unicode nếu có, nếu không thì dùng Arial
    font_name = 'Unicode' if pdf.unicode_font_available else 'Arial'
    pdf.set_font(font_name, '', 14)
    
    temp_dir = "temp_pdf_images"
    os.makedirs(temp_dir, exist_ok=True)
    
    for i, item in enumerate(data_list):
        question_num = i + 1
        
        # --- TRANG 1: ẢNH ĐỀ THI ---
        pdf.add_page()
        font_name = 'Unicode' if pdf.unicode_font_available else 'Arial'
        pdf.set_font(font_name, 'B', 16)
        pdf.cell(0, 10, f"Câu số: {question_num}", ln=True, align='C')
        pdf.ln(5)
        
        if item.get('image_url'):
            temp_img_path = os.path.join(temp_dir, f"temp_img_{question_num}.jpg")
            
            # Tải ảnh về
            if download_image_for_pdf(session, item['image_url'], temp_img_path):
                try:
                    # Mở ảnh và tính toán kích thước
                    with Image.open(temp_img_path) as img:
                        img_width, img_height = img.size
                        aspect_ratio = img_height / img_width
                        
                        # Kích thước tối đa trong PDF (A4: 210x297mm, margin 15mm mỗi bên)
                        max_width_mm = 180
                        max_height_mm = 240
                        
                        # Tính kích thước thực tế
                        width_mm = min(max_width_mm, max_width_mm)
                        height_mm = width_mm * aspect_ratio
                        
                        # Nếu ảnh quá cao, scale lại
                        if height_mm > max_height_mm:
                            height_mm = max_height_mm
                            width_mm = height_mm / aspect_ratio
                        
                        # Chèn ảnh vào PDF (căn giữa)
                        x_position = (210 - width_mm) / 2
                        pdf.image(temp_img_path, x=x_position, y=40, w=width_mm, h=height_mm)
                    
                    # Xóa ảnh tạm
                    if os.path.exists(temp_img_path):
                        os.remove(temp_img_path)
                        
                except Exception as e:
                    print(f"    (!) Lỗi khi xử lý ảnh câu {question_num}: {e}")
            else:
                pdf.set_font(font_name, '', 12)
                pdf.cell(0, 10, f"[Không thể tải ảnh: {item.get('image_url', 'N/A')}]", ln=True)
        else:
            pdf.set_font(font_name, '', 12)
            pdf.cell(0, 10, "[Không có ảnh cho câu hỏi này]", ln=True)
        
        # --- TRANG 2: BÌNH LUẬN/ĐÁP ÁN ---
        pdf.add_page()
        pdf.set_font(font_name, 'B', 14)
        pdf.cell(0, 10, f"Đáp án & Bình luận cho câu {question_num}:", ln=True)
        pdf.ln(5)
        
        comments = item.get('comments', [])
        if not comments:
            pdf.set_font(font_name, '', 12)
            pdf.multi_cell(0, 10, "- Chưa có bình luận/đáp án nào.")
        else:
            pdf.set_font(font_name, '', 12)
            # Giới hạn số lượng comment hiển thị
            max_comments = min(len(comments), config.MAX_COMMENTS_PER_QUESTION)
            for idx, comment in enumerate(comments[:max_comments]):
                try:
                    pdf.multi_cell(0, 8, f"{idx+1}. {comment}")
                except Exception as e:
                    # Nếu vẫn lỗi, thử encode lại text
                    try:
                        safe_comment = comment.encode('ascii', 'ignore').decode('ascii')
                        pdf.multi_cell(0, 8, f"{idx+1}. {safe_comment}")
                    except:
                        pdf.multi_cell(0, 8, f"{idx+1}. [Không thể hiển thị comment này]")
                pdf.ln(2)
            
            if len(comments) > max_comments:
                pdf.set_font(font_name, 'I', 10)
                pdf.cell(0, 8, f"(Hiển thị {max_comments}/{len(comments)} bình luận)", ln=True)
    
    # Xóa thư mục tạm
    try:
        if os.path.exists(temp_dir) and not os.listdir(temp_dir):
            os.rmdir(temp_dir)
    except:
        pass
    
    # Lưu file PDF
    try:
        pdf.output(output_path)
        file_size = os.path.getsize(output_path) / 1024  # KB
        print(f"    [+] PDF đã được tạo: {os.path.basename(output_path)} ({file_size:.1f} KB)")
    except Exception as e:
        print(f"    (!) Lỗi khi lưu file PDF: {e}")
        raise


def create_pdf_from_json_file(session: requests.Session, json_path: str, output_path: str):
    """Tạo PDF từ file JSON đã lưu trước đó."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Chuyển đổi format nếu cần
        data_list = []
        if isinstance(data, dict):
            # Format: {media_id: {image_url, comments, ...}}
            for media_id, item in data.items():
                data_list.append(item)
        elif isinstance(data, list):
            # Format: [{image_url, comments, ...}, ...]
            data_list = data
        
        thread_title = os.path.basename(os.path.dirname(json_path))
        create_pdf_from_data(session, data_list, output_path, thread_title)
        
    except Exception as e:
        print(f"[!] Lỗi khi tạo PDF từ JSON: {e}")

