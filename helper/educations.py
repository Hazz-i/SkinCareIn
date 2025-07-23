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

def generate_pagination_links(base_url, posts_data, current_page=1, max_results=10, prev_link=None):
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
    
    # Prev Link: menggunakan prev_link yang disimpan atau current_link sebagai fallback
    if pagination_info['Prev_Page']:
        if prev_link:
            # Gunakan prev_link yang disimpan dari request sebelumnya
            pagination_info['Prev_Link'] = prev_link
        else:
            pagination_info['Prev_Link'] = None

    return pagination_info

def get_educations_list(page_number=1, url="https://www.eduskincare.eu.org/", prev_link=None):
    """Fungsi utama untuk keseluruhan proses scraping, transformasi data, dan penyimpanan."""
    BASE_URL = 'https://www.eduskincare.eu.org/'

    content = fetching_content(url)
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
                # Extract title and link - try h3 first, then h2
                title_element = article.find('h3') or article.find('h2')
                title = title_element.text.strip() if title_element else ''
                link_element = title_element.find('a') if title_element else None
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
    pagination = generate_pagination_links(BASE_URL, all_posts_data, page_number, max_results=10, prev_link=prev_link)
    
    # Tambahkan current_link ke pagination untuk disimpan di client
    pagination['Current_Link'] = url
    
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
        first_image_removed = False
        first_heading_removed = False
        
        def extract_images_from_element(elem):
            """Extract all images from an element and its children"""
            images = []
            # Find all img tags in the element
            for img in elem.find_all('img'):
                img_src = img.get('src', '')
                img_alt = img.get('alt', '')
                img_title = img.get('title', '')
                
                if img_src:
                    img_attributes = f'src="{img_src}"'
                    if img_alt:
                        img_attributes += f' alt="{img_alt}"'
                    if img_title:
                        img_attributes += f' title="{img_title}"'
                    images.append(f'<img {img_attributes}>')
            return images
        
        def process_element(elem):
            """Recursively process HTML elements and their children"""
            nonlocal first_image_removed, first_heading_removed
            
            if elem.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # Skip the first heading
                if not first_heading_removed:
                    first_heading_removed = True
                    return ''
                
                # Process remaining headings
                if elem.name == 'h1':
                    return f"# {elem.get_text(strip=True)}\n\n"
                elif elem.name == 'h2':
                    return f"## {elem.get_text(strip=True)}\n\n"
                elif elem.name == 'h3':
                    return f"### {elem.get_text(strip=True)}\n\n"
                elif elem.name == 'h4':
                    return f"#### {elem.get_text(strip=True)}\n\n"
                elif elem.name == 'h5':
                    return f"##### {elem.get_text(strip=True)}\n\n"
                elif elem.name == 'h6':
                    return f"###### {elem.get_text(strip=True)}\n\n"
            elif elem.name == 'p':
                # Handle paragraphs that might contain images or other elements
                p_content = []
                
                # First, check if there are any images in this paragraph
                images = extract_images_from_element(elem)
                if images:
                    # Skip the first image if not yet removed
                    if not first_image_removed:
                        first_image_removed = True
                        # Remove the first image from the list
                        images = images[1:] if len(images) > 1 else []
                    
                    # Add remaining images if any
                    if images:
                        p_content.extend(images)
                
                # Get text content, excluding image tags
                text_content = []
                for child in elem.children:
                    if child.name != 'img' and hasattr(child, 'get_text'):
                        text = child.get_text(strip=True)
                        if text:
                            text_content.append(text)
                    elif hasattr(child, 'strip') and child.name != 'img':
                        text = str(child).strip()
                        if text:
                            text_content.append(text)
                
                # Add text content if any
                if text_content:
                    p_content.append(' '.join(text_content))
                
                if p_content:
                    return '\n'.join(p_content) + '\n\n'
                return ''
            elif elem.name == 'img':
                # Handle standalone images - skip the first one
                if not first_image_removed:
                    first_image_removed = True
                    return ''
                
                img_src = elem.get('src', '')
                img_alt = elem.get('alt', '')
                img_title = elem.get('title', '')
                
                if img_src:
                    img_attributes = f'src="{img_src}"'
                    if img_alt:
                        img_attributes += f' alt="{img_alt}"'
                    if img_title:
                        img_attributes += f' title="{img_title}"'
                    return f'<img {img_attributes}>\n\n'
                return ''
            elif elem.name == 'blockquote':
                text = elem.get_text(strip=True)
                if text:
                    return f"> {text}\n\n"
                return ''
            elif elem.name == 'ul':
                ul_content = []
                for li in elem.find_all('li', recursive=False):
                    li_text = li.get_text(strip=True)
                    if li_text:
                        ul_content.append(f"- {li_text}")
                return '\n'.join(ul_content) + '\n\n' if ul_content else ''
            elif elem.name == 'ol':
                ol_content = []
                for i, li in enumerate(elem.find_all('li', recursive=False), 1):
                    li_text = li.get_text(strip=True)
                    if li_text:
                        ol_content.append(f"{i}. {li_text}")
                return '\n'.join(ol_content) + '\n\n' if ol_content else ''
            elif elem.name == 'table':
                # Handle tables
                table_content = []
                
                # Process table headers
                thead = elem.find('thead')
                if thead:
                    header_row = thead.find('tr')
                    if header_row:
                        headers = []
                        for th in header_row.find_all(['th', 'td']):
                            # Check for images in header cells
                            cell_images = extract_images_from_element(th)
                            if cell_images:
                                # Handle first image removal in table cells
                                if not first_image_removed and cell_images:
                                    first_image_removed = True
                                    cell_images = cell_images[1:] if len(cell_images) > 1 else []
                                
                                if cell_images:
                                    headers.append(' '.join(cell_images))
                                else:
                                    headers.append(th.get_text(strip=True))
                            else:
                                headers.append(th.get_text(strip=True))
                        
                        if headers:
                            table_content.append('| ' + ' | '.join(headers) + ' |')
                            table_content.append('|' + '---|' * len(headers))
                
                # Process table body
                tbody = elem.find('tbody') or elem
                for row in tbody.find_all('tr'):
                    cells = []
                    for cell in row.find_all(['td', 'th']):
                        # Check for images in this cell
                        cell_images = extract_images_from_element(cell)
                        if cell_images:
                            # Handle first image removal in table cells
                            if not first_image_removed and cell_images:
                                first_image_removed = True
                                cell_images = cell_images[1:] if len(cell_images) > 1 else []
                            
                            if cell_images:
                                cells.append(' '.join(cell_images))
                            else:
                                cells.append(cell.get_text(strip=True))
                        else:
                            # Otherwise use text content
                            cells.append(cell.get_text(strip=True))
                    
                    if cells:
                        table_content.append('| ' + ' | '.join(cells) + ' |')
                
                return '\n'.join(table_content) + '\n\n' if table_content else ''
            elif elem.name == 'div':
                # Handle divs recursively
                div_content = []
                
                # First check if this div directly contains images
                direct_images = extract_images_from_element(elem)
                if direct_images:
                    # Handle first image removal
                    if not first_image_removed and direct_images:
                        first_image_removed = True
                        direct_images = direct_images[1:] if len(direct_images) > 1 else []
                    
                    if direct_images:
                        div_content.extend(direct_images)
                
                # Then process child elements
                for child in elem.children:
                    if child.name:
                        processed = process_element(child)
                        if processed:
                            div_content.append(processed)
                    elif hasattr(child, 'strip'):
                        text = str(child).strip()
                        if text and not text.startswith('<'):  # Avoid duplicate HTML
                            div_content.append(text + '\n')
                
                return '\n'.join(div_content) if div_content else ''
            else:
                # Handle other elements - check for images first
                images = extract_images_from_element(elem)
                if images:
                    # Handle first image removal
                    if not first_image_removed and images:
                        first_image_removed = True
                        images = images[1:] if len(images) > 1 else []
                    
                    result = ''
                    if images:
                        result = '\n'.join(images) + '\n'
                    
                    text = elem.get_text(strip=True)
                    if text:
                        result += text + '\n'
                    return result
                else:
                    text = elem.get_text(strip=True)
                    if text:
                        return text + '\n'
                    return ''
        
        # Process all children of the main element
        for child in element.children:
            if child.name:
                processed = process_element(child)
                if processed:
                    markdown_content.append(processed)
            elif hasattr(child, 'strip'):
                # Handle plain text nodes (NavigableString)
                try:
                    text = str(child).strip()
                    if text and not text.startswith('<'):  # Avoid duplicate HTML
                        markdown_content.append(text + '\n')
                except:
                    pass
        
        return ''.join(markdown_content)
    
    # Convert content to markdown
    markdown_text = convert_to_markdown(content_div)
    
    # Debug: Check if any images were found in the entire content
    all_images = content_div.find_all('img') if content_div else []
    print(f"Debug: Found {len(all_images)} images in content")
    for i, img in enumerate(all_images):
        print(f"Debug: Image {i+1}: src='{img.get('src', '')}', alt='{img.get('alt', '')}'")
    
    # Create final data structure
    education_data = {
        'Title': title,
        'Author': author,
        'Date': parse_date(date),
        'Cover_Image': imgUrl,
        'Content': markdown_text,
    }

    return education_data