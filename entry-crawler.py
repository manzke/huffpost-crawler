import json
import httpx
from bs4 import BeautifulSoup
import os
import time
import signal
import aiofiles
from datetime import datetime, timezone
import asyncio

REQUEST_LIMIT = 250
REQUEST_DELAY = 0.1  # Delay in seconds between requests
LOG_INTERVAL = 10  # Log diagnostics every 10 requests
SESSION_RESTART_DELAY = 5  # Delay in seconds when the session is restarted

session = None
shutdown_event = asyncio.Event()

async def extract_full_text_and_metadata(url, session, error_file_path):
    try:
        id = url.split('_')[-1]
        response = await session.get(url)
        if response.is_redirect:
            redirect_url = response.headers["location"]
            if "/entry/" not in redirect_url:
                raise httpx.RequestError("Redirect detected. Please check the URL.")
            else:
                response = await session.get(redirect_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')

        metadata = {
            'title': '',
            'description': '',
            'language': soup.find('html')['lang'] if soup.find('html') and 'lang' in soup.find('html').attrs else '',
            'date-crawled': datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        }

        if response.is_redirect:
            metadata['redirect_url'] = redirect_url

        ld_json_script = soup.find('script', type='application/ld+json')
        if ld_json_script:
            ld_json = json.loads(ld_json_script.string)
            metadata.update({
                'description': ld_json.get('description', ''),
                'title': ld_json.get('headline', ''),
                'keywords': ','.join(ld_json.get('keywords', [])),
                'section': ld_json.get('articleSection', ''),
                'date-created': ld_json.get('dateCreated', ''),
                'date-modified': ld_json.get('dateModified', ''),
                'date-published': ld_json.get('datePublished', ''),
                'language': metadata['language'] or ld_json.get('inLanguage', '')
            })

            author_info = ld_json.get('author')
            if isinstance(author_info, list):
                if len(author_info) > 0 and isinstance(author_info[0], dict):
                    metadata['author'] = author_info[0].get('name', '')
                    metadata['author-description'] = author_info[0].get('description', '')
            elif isinstance(author_info, dict):
                metadata['author'] = author_info.get('name', '')
                metadata['author-description'] = author_info.get('description', '')

        def update_metadata_if_empty(meta_key, meta_property):
            if not metadata[meta_key]:
                meta_tag = soup.find('meta', attrs={'property': meta_property})
                if meta_tag and 'content' in meta_tag.attrs:
                    metadata[meta_key] = meta_tag['content']

        update_metadata_if_empty('title', 'og:title')
        update_metadata_if_empty('description', 'og:description')
        update_metadata_if_empty('keywords', 'article:tag')
        update_metadata_if_empty('section', 'article:section')
        update_metadata_if_empty('date-published', 'article:published_time')
        update_metadata_if_empty('date-modified', 'article:modified_time')
        if not metadata['description']:
            description_meta = soup.find('meta', attrs={'name': 'description'})
            if description_meta and 'content' in description_meta.attrs:
                metadata['description'] = description_meta['content']

        article = soup.find('article')
        if not article:
            print(f"No article tag found in {url}")
            return None, metadata, id
        
        article_text = ''
        for article in soup.find_all('article'):
            for div in article.find_all('div', {'id': 'support-huffpost-entry'}):
                div.decompose()
            for aside in article.find_all('aside', class_='entry__right-rail'):
                aside.decompose()
            for paragraph in article.find_all('p'):
                if paragraph.get_text(strip=True):
                    article_text += paragraph.get_text(strip=True) + '\n'
        
        return article_text.strip(), metadata, id
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 428:
            print(f"HTTP 428 Precondition Required for URL {url}")
        else:
            print(f"HTTP error {e.response.status_code} for URL {url}")
        result = {
            'id': id,
            'link': url,
            'message': f"HTTP error {e.response.status_code} for URL {url}: {e}"
        }
        async with aiofiles.open(error_file_path, 'a') as errorfile:
            await errorfile.write(json.dumps(result) + '\n')
        return None, None, None    
    except httpx.RequestError as e:
        print(f"Error fetching URL {url}: {e}")
        result = {
            'id': id,
            'link': url,
            'message': f"Error fetching URL {url}: {e}"
        }
        async with aiofiles.open(error_file_path, 'a') as errorfile:
            await errorfile.write(json.dumps(result) + '\n')
        return None, None, None    

def load_processed_links(filepath):
    processed_links = set()
    if os.path.exists(filepath):
        with open(filepath, 'r') as existingfile:
            for line in existingfile:
                data = json.loads(line)
                processed_links.add(data['link'])
    return processed_links

async def graceful_shutdown():
    print("Gracefully shutting down...")
    shutdown_event.set()
    if session:
        await session.aclose()
    print("Resources have been released.")

def signal_handler(signum, frame):
    asyncio.create_task(graceful_shutdown())

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)

file_path = 'unique_links-2024-05-28.json'
error_file_path = f'articles-errors-{file_path}'
output_file_path = f'articles-{file_path}'

processed_links = load_processed_links(output_file_path) | load_processed_links(error_file_path)

async def main():
    global session

    async with httpx.AsyncClient(http2=True) as session:
        async with aiofiles.open(output_file_path, 'a') as outfile, aiofiles.open(error_file_path, 'a') as errorfile:
            async with aiofiles.open(file_path, 'r') as file:
                json_lines = await file.readlines()

            filtered_json_lines = [line for line in json_lines if json.loads(line)['link'] not in processed_links]
            print(f"Filtered {len(json_lines) - len(filtered_json_lines)} duplicate articles")

            total_lines = len(filtered_json_lines)
            request_count = 0
            time_since_last_log = time.time()

            for i, line in enumerate(filtered_json_lines):
                if shutdown_event.is_set():
                    print("Shutdown event set, stopping processing.")
                    break

                if request_count >= REQUEST_LIMIT:
                    await session.aclose()
                    print(f"Session limit reached. Pausing for {SESSION_RESTART_DELAY} seconds.")
                    await asyncio.sleep(SESSION_RESTART_DELAY)
                    session = httpx.AsyncClient(http2=True)
                    request_count = 0

                start_time = time.time()
                data = json.loads(line)
                url = data['link']
                print(f"Processing URL: {url}")
                full_text, metadata, id = await extract_full_text_and_metadata(url, session, error_file_path)
                
                if full_text:
                    result = {
                        'id': id,
                        'link': url,
                        'redirect_url': metadata.get('redirect_url', ''),
                        'title': metadata['title'],
                        'description': metadata['description'],
                        'keywords': metadata['keywords'],
                        'section': metadata['section'],
                        'author': metadata['author'],
                        'author-description': metadata['author-description'],
                        'date-created': metadata['date-created'],
                        'date-crawled': metadata['date-crawled'],
                        'date-modified': metadata['date-modified'],
                        'date-published': metadata['date-published'],
                        'language': metadata['language'],
                        'content': full_text
                    }
                    await outfile.write(json.dumps(result) + '\n')
                
                request_count += 1
                elapsed_time = time.time() - start_time
                await asyncio.sleep(REQUEST_DELAY)  # Delay to avoid rate limits

                if i % LOG_INTERVAL == 0:
                    print(f"Processed {i + 1}/{total_lines} lines. Last {url}")
                    print(f"Time taken for last request: {elapsed_time:.2f} seconds")
                    print(f"Time till last log: {time.time() - time_since_last_log:.2f} seconds")
                    print(f"Total requests so far: {request_count}")
                    time_since_last_log = time.time()

print(f"Articles have been saved to {output_file_path}")

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(main())
finally:
    loop.run_until_complete(graceful_shutdown())
    loop.close()
