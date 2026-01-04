# library/thread_utils.py

import re
from urllib.parse import urlparse
from typing import Dict

def extract_thread_info_from_url(url: str) -> Dict[str, str]:
    """
    Extract thông tin từ URL của thread.
    
    Ví dụ: https://fuoverflow.com/threads/csi106-fa25-re.5577/
    -> {
        'thread_id': '5577',
        'slug': 'csi106-fa25-re.5577',
        'base_url': 'https://fuoverflow.com'
    }
    
    Args:
        url: URL của thread
    
    Returns:
        Dict chứa thread_id, slug, base_url, url
    """
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    # Extract thread ID và slug từ path
    # Pattern: /threads/[slug].[id]/
    match = re.search(r'/threads/([^/]+)\.(\d+)/?', parsed.path)
    
    if match:
        slug = match.group(1)
        thread_id = match.group(2)
        full_slug = f"{slug}.{thread_id}"
    else:
        # Fallback: nếu không match pattern, dùng path làm slug
        slug = parsed.path.strip('/').split('/')[-1]
        thread_id = slug.split('.')[-1] if '.' in slug else None
        full_slug = slug
    
    return {
        'thread_id': thread_id,
        'slug': full_slug,
        'base_url': base_url,
        'url': url
    }

def normalize_url(url: str) -> str:
    """
    Chuẩn hóa URL (loại bỏ trailing slash, giữ lại query params nếu cần).
    
    Args:
        url: URL cần chuẩn hóa
    
    Returns:
        URL đã được chuẩn hóa
    """
    # Loại bỏ trailing slash
    url = url.rstrip('/')
    # Giữ lại URL gốc, chỉ normalize trailing slash
    return url


