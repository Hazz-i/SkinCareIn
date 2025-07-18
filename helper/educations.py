from bs4 import BeautifulSoup
from helper import fetching_content

import datetime

def parse_date_from_metadata(metadata_list):
    """Extract and parse date from metadata list"""
    if not metadata_list:
        return None
    
    # Ambil item terakhir dari list metadata
    date_str = metadata_list[1] if metadata_list else ''
    
    # Skip jika hanya angka tunggal
    if date_str.isdigit() and len(date_str) <= 2:
        return None
    
    # Daftar format tanggal yang mungkin
    date_formats = [
        '%d %B, %Y',    # 22 May, 2025
        '%d %B %Y',     # 22 May 2025
        '%d %b, %Y',    # 7 Jul, 2025
        '%d %b %Y',     # 7 Jul 2025
        '%B %d, %Y',    # May 22, 2025
        '%b %d, %Y',    # Jul 7, 2025
        '%Y-%m-%d',     # 2025-05-22
        '%d/%m/%Y',     # 22/05/2025
        '%m/%d/%Y',     # 05/22/2025
    ]
    
    for date_format in date_formats:
        try:
            date_obj = datetime.datetime.strptime(date_str, date_format)
            return date_obj
        except ValueError:
            continue
    
    # Jika semua format gagal
    print(f"Could not parse date: {date_str}")
    return None

def parse_date(date):
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


def create_search_url(base_url, date_obj, page_number=1, max_results=10):
    """Create search URL for pagination if needed"""
    if date_obj:
        date_format = date_obj.strftime('%Y-%m-%d')  # Format: 2025-05-22
        return f'{base_url}search?updated-max={date_format}T18:26:00%2B07:00&max-results={max_results}&page={page_number}'
    else:
        # Fallback URL tanpa filter tanggal
        return f'{base_url}search?max-results={max_results}&page={page_number}'

def generate_pagination_links(base_url, posts_data, current_page=1, max_results=10):
    """Generate next and prev pagination links based on posts data"""
    pagination_info = {
        'Current_Page': str(current_page),
        'Prev_Page': str(current_page - 1) if current_page > 1 else None,
        'Prev_Link': None,
        'Next_Page': str(current_page + 1),
        'Next_Link': None,
    }
    
    if not posts_data:
        return pagination_info
    
    # Next Link: menggunakan tanggal dari post terakhir ([-1])
    last_post = posts_data[-1]
    if last_post.get('Date'):
        try:
            # Parse tanggal dari format YYYY-MM-DD
            next_link = f'{base_url}search?updated-max={last_post["Date"]}T18:26:00%2B07:00&max-results={max_results}&page={pagination_info["Next_Page"]}'
            pagination_info['Next_Link'] = next_link
        except ValueError:
            pass
    
    # Prev Link: menggunakan tanggal dari post pertama ([0])
    if pagination_info['Prev_Page']:
        first_post = posts_data[0]
        if first_post.get('Date'):
            try:
                prev_link = f'{base_url}search?updated-max={first_post["Date"]}T18:26:00%2B07:00&max-results={max_results}&page={pagination_info["Prev_Page"]}'
                pagination_info['Prev_Link'] = prev_link
            except ValueError:
                pass
    
    return pagination_info

def get_educations_list(page_number=1):
    """Fungsi utama untuk keseluruhan proses scraping, transformasi data, dan penyimpanan."""
    BASE_URL = 'https://www.eduskincare.eu.org/'
    
    content = fetching_content(BASE_URL)
    if not content:
        print("Failed to fetch content. Stopping.")
        return [], {}
    
    soup = BeautifulSoup(content, "html.parser")
    
    # Array untuk menyimpan semua data
    all_posts_data = []
    
    try:
        # Scrape dari widget-content feature-posts
        top_edu = soup.find('div', class_='widget-content feature-posts')
        if top_edu:
            item_posts = top_edu.find_all('div', class_='item-post')
            
            for post in item_posts:
                try:
                    # Extract image - check for lazy loading attributes
                    img_element = post.find('img')
                    img_src = ''
                    
                    if img_element:
                        # Check for actual image URL in various attributes
                        if img_element.get('data-src'):
                            img_src = img_element['data-src']
                        elif img_element.get('data-lazy-src'):
                            img_src = img_element['data-lazy-src']
                        elif img_element.get('data-original'):
                            img_src = img_element['data-original']
                        elif img_element.get('src') and not img_element['src'].startswith('data:'):
                            img_src = img_element['src']
                    
                    # Extract title and link
                    title = post.find('h3').text.strip() if post.find('h3') else ''
                    link_element = post.find('h3').find('a') if post.find('h3') else None
                    link = link_element['href'] if link_element else ''

                    # Extract snippet/description
                    descriptions = post.find('p', class_='item-snippet')
                    descriptions = descriptions.text.strip() if descriptions else ''
                    
                    # Extract metadata (small tags)
                    meta_elements = post.find_all('small')
                    meta_data = [meta.text.strip() for meta in meta_elements if meta.text.strip()]
                    
                    # Parse date from metadata
                    parsed_date = parse_date_from_metadata(meta_data)
                    formatted_date = parsed_date.strftime('%Y-%m-%d') if parsed_date else ''
                    
                    post_data = {
                        'Title': title,
                        'Link': link,
                        'Image': img_src,
                        'Snippet': descriptions,
                        'Date': formatted_date,
                        'Category': 'feature-posts'
                    }
                    
                    all_posts_data.append(post_data)
                    
                except Exception as e:
                    print(f"Error processing feature post: {e}")
                    continue

        articles = soup.find_all('article', class_='item-post mb-4')

        for article in articles:
            try:
                title = article.find('h3').text.strip() if article.find('h3') else ''
                link_element = article.find('h3').find('a') if article.find('h3') else None
                link = link_element['href'] if link_element else ''
                
                # Extract image
                img_element = article.find('img')
                img_src = ''
                
                if img_element:
                    # Check for actual image URL in various attributes
                    if img_element.get('data-src'):
                        img_src = img_element['data-src']
                    elif img_element.get('data-lazy-src'):
                        img_src = img_element['data-lazy-src']
                    elif img_element.get('data-original'):
                        img_src = img_element['data-original']
                    elif img_element.get('src') and not img_element['src'].startswith('data:'):
                        img_src = img_element['src']
                
                descriptions = article.find('p', class_='item-snippet').text.strip() if article.find('p', class_='item-snippet') else ''
                meta_data = [meta.text.strip() for meta in article.find_all('small') if meta.text.strip()]

                # Parse date from metadata
                parsed_date = parse_date_from_metadata(meta_data)
                formatted_date = parsed_date.strftime('%Y-%m-%d') if parsed_date else ''

                post_data = {
                    'Title': title,
                    'Link': link,
                    'Image': img_src,
                    'Snippet': descriptions,
                    'Date': formatted_date,
                    'Category': 'article-items'
                }
                
                all_posts_data.append(post_data)
                
            except Exception as e:
                print(f"Error processing article: {e}")
                continue

    except Exception as e:
        print(f"Error during scraping: {e}")
        return [], {}

    # Generate pagination links
    pagination = generate_pagination_links(BASE_URL, all_posts_data, page_number, max_results=10)
    
    data = {
        "Educations_List": all_posts_data,
        "Pagination": pagination
    }

    return data

def get_educations_details(url):
    """Fungsi untuk mengambil detail pendidikan dari halaman utama."""
    
    content = fetching_content(url)
    if not content:
        print("Failed to fetch content. Stopping.")
        return [], {}
    
    soup = BeautifulSoup(content, "html.parser")
    title = soup.find('h1').text.strip() if soup.find('h1') else 'No Title Found'
    author = soup.find('div', class_='me-3').text.strip() if soup.find('div', class_='me-3') else 'No Author Found'
    date = soup.find('span', class_='date-format').text.strip() if soup.find('span', class_='date-format') else 'No Date Found'
    imgUrl = soup.find_all('img')[1]['src'] if len(soup.find_all('img')) > 1 else 'No Image Found'
    
    content_div = soup.find('div', class_='entry-text text-break mb-5')
    
    if not content_div:
        print("Content div not found!")
        return [], {}
    
    # Function to convert content to markdown
    def convert_to_markdown(element):
        markdown_content = []
        img_counter = 0  # Counter untuk melacak gambar
        
        for child in element.children:
            if child.name == 'h1':
                markdown_content.append(f"# {child.get_text(strip=True)}\n")
            elif child.name == 'h2':
                markdown_content.append(f"## {child.get_text(strip=True)}\n")
            elif child.name == 'h3':
                markdown_content.append(f"### {child.get_text(strip=True)}\n")
            elif child.name == 'h4':
                markdown_content.append(f"#### {child.get_text(strip=True)}\n")
            elif child.name == 'h5':
                markdown_content.append(f"##### {child.get_text(strip=True)}\n")
            elif child.name == 'h6':
                markdown_content.append(f"###### {child.get_text(strip=True)}\n")
            elif child.name == 'p':
                text = child.get_text(strip=True)
                if text:
                    markdown_content.append(f"{text}\n")
            elif child.name == 'img':
                img_counter += 1
                if img_counter > 1:  # Skip first image
                    img_src = child.get('src', '')
                    img_alt = child.get('alt', '')
                    if img_src:
                        markdown_content.append(f"![{img_alt}]({img_src})\n")
            elif child.name == 'blockquote':
                text = child.get_text(strip=True)
                if text:
                    markdown_content.append(f"> {text}\n")
            elif child.name == 'ul':
                for li in child.find_all('li'):
                    li_text = li.get_text(strip=True)
                    if li_text:
                        markdown_content.append(f"- {li_text}\n")
            elif child.name == 'ol':
                for i, li in enumerate(child.find_all('li'), 1):
                    li_text = li.get_text(strip=True)
                    if li_text:
                        markdown_content.append(f"{i}. {li_text}\n")
            elif child.name == 'div':
                # Handle nested divs
                div_text = child.get_text(strip=True)
                if div_text:
                    markdown_content.append(f"{div_text}\n")
            elif child.name and child.get_text(strip=True):
                # Handle other tags as plain text
                text = child.get_text(strip=True)
                markdown_content.append(f"{text}\n")
            elif hasattr(child, 'strip'):
                # Handle plain text nodes (NavigableString)
                try:
                    text = str(child).strip()
                    if text:
                        markdown_content.append(f"{text}\n")
                except:
                    pass
        
        return '\n'.join(markdown_content)
    
    # Convert content to markdown
    markdown_text = convert_to_markdown(content_div)
    
    # Also extract all images separately for reference (skip first image)
    all_images = content_div.find_all('img')
    image_list = []
    for i, img in enumerate(all_images):
        if i == 0:  # Skip first image
            continue
        img_data = {
            'src': img.get('src', ''),
            'alt': img.get('alt', ''),
            'title': img.get('title', '')
        }
        image_list.append(img_data)
    
    # Create final data structure
    education_data = {
        'Title': title,
        'Author': author,
        'Date': parse_date(date),
        'Cover_Image': imgUrl,
        'Content': markdown_text,
        'Images': image_list,
    }

    return education_data