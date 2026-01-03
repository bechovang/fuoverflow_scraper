# scraper/media_api.py

import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlencode
from typing import Optional, Dict, List, Tuple
import config


def get_csrf_token(soup: BeautifulSoup) -> Optional[str]:
    """
    Trích xuất CSRF Token (_xfToken) từ HTML của trang thread.
    XenForo lưu token trong thuộc tính data-csrf của thẻ html hoặc input hidden.
    """
    # Phương pháp 1: Tìm trong thuộc tính data-csrf của thẻ html
    html_tag = soup.find('html')
    if html_tag and html_tag.has_attr('data-csrf'):
        return html_tag['data-csrf']
    
    # Phương pháp 2: Tìm trong input hidden có name="_xfToken"
    token_input = soup.find('input', {'name': '_xfToken'})
    if token_input and token_input.has_attr('value'):
        return token_input['value']
    
    # Phương pháp 3: Tìm trong meta tag
    meta_token = soup.find('meta', {'name': 'csrf-token'})
    if meta_token and meta_token.has_attr('content'):
        return meta_token['content']
    
    return None


def extract_media_ids_from_thread(session: requests.Session, thread_url: str) -> Tuple[List[Dict[str, str]], Optional[str]]:
    """
    Trích xuất danh sách Media IDs từ trang thread và CSRF token.
    Trả về tuple: (list các dict chứa media_id, media_url, filename, csrf_token).
    """
    try:
        response = session.get(thread_url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Lấy CSRF token từ trang thread
        csrf_token = get_csrf_token(soup)
        
        # Tìm tất cả các link có chứa /media/ hoặc có data-lb-sidebar-href
        media_items = []
        
        # Phương pháp 1: Tìm qua data-lb-sidebar-href (lightbox)
        lightbox_links = soup.select('a[data-lb-sidebar-href]')
        for link in lightbox_links:
            sidebar_href = link.get('data-lb-sidebar-href', '')
            if '/media/' in sidebar_href:
                # Trích xuất media ID từ URL (ví dụ: /media/q1-webp.117803/ -> 117803)
                match = re.search(r'/media/[^/]+\.(\d+)/', sidebar_href)
                if match:
                    media_id = match.group(1)
                    base_url = config.FORUM_URL.split('/forums/')[0] if '/forums/' in config.FORUM_URL else config.FORUM_URL
                    base_url = base_url.split('/threads/')[0] if '/threads/' in base_url else base_url
                    if not base_url.startswith('http'):
                        base_url = 'https://fuoverflow.com'
                    media_url = urljoin(base_url, sidebar_href.split('?')[0])
                    
                    # Lấy tên file từ link hoặc span
                    filename_span = link.find('span', class_='file-name')
                    filename = filename_span.text.strip() if filename_span else f"media_{media_id}"
                    
                    media_items.append({
                        'media_id': media_id,
                        'media_url': media_url,
                        'filename': filename
                    })
        
        # Phương pháp 2: Tìm qua attachmentList (fallback)
        if not media_items:
            attachment_links = soup.select('ul.attachmentList a.file-preview.js-lbImage')
            for link in attachment_links:
                href = link.get('href', '')
                if '/media/' in href:
                    match = re.search(r'/media/[^/]+\.(\d+)/', href)
                    if match:
                        media_id = match.group(1)
                        base_url = config.FORUM_URL.split('/forums/')[0] if '/forums/' in config.FORUM_URL else config.FORUM_URL
                        base_url = base_url.split('/threads/')[0] if '/threads/' in base_url else base_url
                        if not base_url.startswith('http'):
                            base_url = 'https://fuoverflow.com'
                        media_url = urljoin(base_url, href.split('?')[0])
                        filename_span = link.find('span', class_='file-name')
                        filename = filename_span.text.strip() if filename_span else f"media_{media_id}"
                        
                        # Tránh trùng lặp
                        if not any(item['media_id'] == media_id for item in media_items):
                            media_items.append({
                                'media_id': media_id,
                                'media_url': media_url,
                                'filename': filename
                            })
        
        return media_items, csrf_token
        
    except Exception as e:
        print(f"    (!) Lỗi khi trích xuất Media IDs: {e}")
        return [], None


def get_media_data_from_json_api(session: requests.Session, media_id: str, csrf_token: Optional[str] = None) -> Optional[Dict]:
    """
    Gọi JSON API để lấy dữ liệu ảnh và comments từ media ID.
    Trả về dict chứa image_url, comments, title hoặc None nếu lỗi.
    
    Args:
        session: requests.Session với cookies đã được cấu hình
        media_id: Media ID (ví dụ: "117803")
        csrf_token: CSRF token (_xfToken) từ trang thread
    """
    # Xây dựng URL API với format chuẩn: /media/item.{id}/
    base_url = config.FORUM_URL.split('/threads/')[0] if '/threads/' in config.FORUM_URL else config.FORUM_URL
    base_url = base_url.split('/forums/')[0] if '/forums/' in base_url else base_url
    if not base_url.startswith('http'):
        base_url = 'https://fuoverflow.com'
    
    # Sử dụng format chuẩn: /media/item.{id}/
    api_url = f"{base_url.rstrip('/')}/media/item.{media_id}/"
    
    # Thêm tham số _xfResponseType=json và _xfToken
    params = {'_xfResponseType': 'json'}
    if csrf_token:
        params['_xfToken'] = csrf_token
    
    # Build URL với query parameters
    api_url = f"{api_url}?{urlencode(params)}"
    
    headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': base_url
    }
    
    try:
        response = session.get(api_url, headers=headers, timeout=20)
        response.raise_for_status()
        
        data = response.json()
        
        # Kiểm tra cấu trúc JSON trả về
        if 'html' not in data or 'content' not in data['html']:
            print(f"    (!) Cấu trúc JSON không đúng từ {api_url}")
            return None
        
        html_content = data['html']['content']
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. Lấy link ảnh gốc (chất lượng cao)
        img_url = None
        
        # Thử nhiều selector khác nhau
        img_selectors = [
            '.attachedImage img',
            '.media-container img',
            '.mediaItem img',
            'img[data-src]',
            'img[src]'
        ]
        
        for selector in img_selectors:
            img_tag = soup.select_one(selector)
            if img_tag:
                img_url = img_tag.get('data-src') or img_tag.get('src')
                if img_url:
                    # Chuyển đổi relative URL thành absolute
                    if not img_url.startswith('http'):
                        base_url = config.FORUM_URL.split('/threads/')[0] if '/threads/' in config.FORUM_URL else config.FORUM_URL
                        base_url = base_url.split('/forums/')[0] if '/forums/' in base_url else base_url
                        if not base_url.startswith('http'):
                            base_url = 'https://fuoverflow.com'
                        img_url = urljoin(base_url, img_url)
                    break
        
        # 2. Lấy tiêu đề/câu hỏi
        title = None
        title_selectors = ['.p-title-value', '.media-title', 'h1']
        for selector in title_selectors:
            title_tag = soup.select_one(selector)
            if title_tag:
                title = title_tag.get_text(strip=True)
                break
        
        # 3. Lấy tất cả comments
        comments = []
        comment_selectors = [
            '.comment-body .bbWrapper',
            '.comment-content .bbWrapper',
            '.message-body .bbWrapper',
            '.comment .bbWrapper'
        ]
        
        for selector in comment_selectors:
            comment_tags = soup.select(selector)
            if comment_tags:
                for tag in comment_tags:
                    comment_text = tag.get_text(strip=True)
                    if comment_text and comment_text not in comments:
                        comments.append(comment_text)
                break
        
        return {
            'image_url': img_url,
            'title': title or 'Unknown',
            'comments': comments
        }
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            print(f"    (!) Lỗi 400 Bad Request từ {api_url}")
            if not csrf_token:
                print(f"    (!) Có thể do thiếu CSRF token. Kiểm tra lại cookie.")
            else:
                print(f"    (!) CSRF token có thể đã hết hạn. Vui lòng cập nhật cookie mới.")
        else:
            print(f"    (!) Lỗi HTTP {e.response.status_code} từ {api_url}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"    (!) Lỗi khi gọi JSON API {api_url}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"    (!) Lỗi parse JSON từ {api_url}: {e}")
        return None
    except Exception as e:
        print(f"    (!) Lỗi không xác định khi xử lý {api_url}: {e}")
        return None

