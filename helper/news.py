from helper import fetching_content
from bs4 import BeautifulSoup
import datetime

def parse_date_from_metadata(date):
    """Extract and parse date from metadata list"""
    if not date:
        return date
    
    # Mapping bulan Indonesia ke English
    month_mapping = {
        'januari': 'January', 'februari': 'February', 'maret': 'March',
        'april': 'April', 'mei': 'May', 'juni': 'June',
        'juli': 'July', 'agustus': 'August', 'september': 'September',
        'oktober': 'October', 'november': 'November', 'desember': 'December',
        'jan': 'Jan', 'feb': 'Feb', 'mar': 'Mar', 'apr': 'Apr',
        'jun': 'Jun', 'jul': 'Jul', 'agu': 'Aug', 'sep': 'Sep',
        'okt': 'Oct', 'nov': 'Nov', 'des': 'Dec'
    }
    
    # Convert Indonesian month names to English
    date_english = date.lower()
    for indo_month, eng_month in month_mapping.items():
        date_english = date_english.replace(indo_month, eng_month)
    
    # Capitalize first letter of each word
    date_english = ' '.join(word.capitalize() for word in date_english.split())
    
    # Daftar format tanggal yang mungkin
    date_formats = [
        '%d %B %Y',     # 27 July 2025
        '%d %b %Y',     # 27 Jul 2025
        '%d %B, %Y',    # 27 July, 2025
        '%d %b, %Y',    # 27 Jul, 2025
        '%B %d, %Y',    # July 27, 2025
        '%b %d, %Y',    # Jul 27, 2025
        '%Y-%m-%d',     # 2025-07-27
        '%d/%m/%Y',     # 27/07/2025
        '%m/%d/%Y',     # 07/27/2025
    ]
    
    for date_format in date_formats:
        try:
            date_obj = datetime.datetime.strptime(date_english, date_format)
            # Return in YYYY-MM-DD format
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # Jika semua format gagal, return original date
    print(f"Could not parse date: {date}")
    return date

def get_news_list(page=1):
    """Mengambil daftar berita dari URL yang diberikan."""

    BASE_URL = f'https://www.kompas.com/tag/skincare?type=artikel&page={page}'

    content = fetching_content(BASE_URL)
    if not content:
        print("Failed to fetch content. Stopping.")

    soup = BeautifulSoup(content, "html.parser")
    article_elements = soup.find_all('div', class_='articleItem')

    # Mencari semua elemen dengan atribut data-ci-pagination-page
    page_elements = soup.find_all(attrs={'data-ci-pagination-page': True})
    page_number_list = []

    for pages in page_elements:
        page_attr = pages.get('data-ci-pagination-page')
        if page_attr and page_attr.isdigit():
            page_number_list.append(page_attr)

    # Mengurutkan dan mengonversi ke integer lalu kembali ke string untuk konsistensi
    page_number_list = sorted(set(page_number_list), key=int)

    paginations = {
        'Current_Page': str(page),
        'First_Page': str(page_number_list[0]) if page > 1 else None,
        'Prev_Page': str(page - 1) if page > 1 else None,
        'Next_Page': str(page + 1) if page < 70 else None,
        'Last_Page': str(page_number_list[-1]) if page < 70 else None
    }

    print(f"Jumlah artikel yang ditemukan: {len(article_elements)}")

    article_list = []
    for article in article_elements:
        title = article.find('h2', class_='articleTitle').text.strip()
        link = article.find('a')['href']
        img = article.find('img')['src'] if article.find('img') else ''
        
        # Extract date from articlePost-date
        post_elements = article.find('div', class_='articlePost')
        date = ''
        category = ''
        
        if post_elements:
            # Extract date
            date_element = post_elements.find('div', class_='articlePost-date')
            if date_element:
                date = date_element.text.strip()
            
            # Extract category from articlePost-subtitle
            category_element = post_elements.find('div', class_='articlePost-subtitle')
            if category_element:
                category = category_element.text.strip()
        
        article_list.append({
            'Title': title,
            'Link': link,
            'Image': img,
            'Date': parse_date_from_metadata(date) if date else date,
            'Category': category
        })
        
    
    data = {
        'Article_List': article_list,
        'Pagination': paginations
    }
        
    return data

def get_news(url):
    """Mengambil detail berita dari URL yang diberikan."""
    
    content = fetching_content(url)
    if not content:
        print("Failed to fetch content. Stopping.")
        return
    
    soup = BeautifulSoup(content, "html.parser")
    pagination = soup.find('div', class_='read__paging clearfix')
    
    data = []

    if pagination:
        print("Pagination found.")
        print('-' *20)
        url = url + '?page=all'
        
        content = fetching_content(url)
        if not content:
            print("Failed to fetch content. Stopping.")
            return
        
        title = soup.find('h1', class_='read__title').text.strip()
        
        photo_wrap = soup.find('div', class_='photo__wrap')
        cover_image = ''
        if photo_wrap:
            img_element = photo_wrap.find('img')
            if img_element and img_element.get('src'):
                cover_image = img_element['src']

        time_elements = soup.find('div', class_='read__time').text.strip()
        source = time_elements.split(' - ')[0].strip()
        date = time_elements.split(' - ')[1].strip() if ' - ' in time_elements else ''
        
        author = soup.find('div', class_='credit-title-nameEditor').text.strip()
        
        content_elements = soup.find('div', class_='read__content')
        content_paragraphs = content_elements.find_all('p') 
        if not content_paragraphs:
            print("No paragraphs found in content.")

        # Extract text from all paragraph elements and format as Markdown
        content_text = []
        for p in content_paragraphs:
            # Remove any img tags from the paragraph
            for img in p.find_all('img'):
                img.decompose()
            
            # Get text content and strip whitespace
            text = p.get_text(strip=True)
            if text:  # Only add non-empty text
                # Format as Markdown paragraph
                content_text.append(text)
        
        # Join all paragraphs with double line breaks for Markdown formatting
        full_content = '\n\n'.join(content_text)
        
        # Content in Markdown format (only the content, not metadata)
        print(f"Number of paragraphs found: {len(content_text)}")
        
        data.append({
            'Title': title,
            'ImageUrl': cover_image,
            'Date': parse_date_from_metadata(date),
            'Source': source,
            'Author': author,
            'Content': full_content,
        })
        
    else:
        print("No pagination found.")
        print("-" * 20)
        
        title = soup.find('h1', class_='read__title').text.strip()
        
        photo_wrap = soup.find('div', class_='photo__wrap')
        cover_image = ''
        if photo_wrap:
            img_element = photo_wrap.find('img')
            if img_element and img_element.get('src'):
                cover_image = img_element['src']

        time_elements = soup.find('div', class_='read__time').text.strip()
        source = time_elements.split(' - ')[0].strip()
        date = time_elements.split(' - ')[1].strip() if ' - ' in time_elements else ''
        
        author = soup.find('div', class_='credit-title-nameEditor').text.strip()
        
        content_elements = soup.find('div', class_='read__content')
        content_paragraphs = content_elements.find_all('p') 
        if not content_paragraphs:
            print("No paragraphs found in content.")

        # Extract text from all paragraph elements and format as Markdown
        content_text = []
        for p in content_paragraphs:
            # Remove any img tags from the paragraph
            for img in p.find_all('img'):
                img.decompose()
            
            # Get text content and strip whitespace
            text = p.get_text(strip=True)
            if text:  # Only add non-empty text
                # Format as Markdown paragraph
                content_text.append(text)
        
        # Join all paragraphs with double line breaks for Markdown formatting
        full_content = '\n\n'.join(content_text)
        
        # Content in Markdown format (only the content, not metadata)
        print(f"Number of paragraphs found: {len(content_text)}")
        
        data.append({
            'Title': title,
            'ImageUrl': cover_image,
            'Date': parse_date_from_metadata(date),
            'Source': source,
            'Author': author,
            'Content': full_content,
        })
    
    return data