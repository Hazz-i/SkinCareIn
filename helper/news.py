import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    )
}

def fetching_content(url):
    """Mengambil konten HTML dari URL yang diberikan."""
    session = requests.Session()
    
    try:
        response = session.get(url, headers=HEADERS)
        response.raise_for_status()  # Raise an exception for 4xx/5xx responses
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Terjadi kesalahan ketika melakukan requests terhadap {url}: {e}")
        return None

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

    for page in page_elements:
        page_attr = page.get('data-ci-pagination-page')
        if page_attr and page_attr.isdigit():
            page_number_list.append(page_attr)

    # Mengurutkan dan mengonversi ke integer lalu kembali ke string untuk konsistensi
    page_number_list = sorted(set(page_number_list), key=int)

    print(f"Jumlah halaman yang ditemukan: {page_number_list}")
    print(f"Page numbers from data-ci-pagination-page: {page_number_list}")

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
            'Date': date,
            'Category': category
        })
        
    data = {
        'article_list': article_list,
        'Page Numbers': page_number_list
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
            'Date': date,
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
            'Date': date,
            'Source': source,
            'Author': author,
            'Content': full_content,
        })
    
    return data