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