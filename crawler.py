import requests
import json
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import os

def find_sitemaps(content):
    sitemaps = []
    lines = content.split('\n')
    for line in lines:
        if line.startswith('Sitemap:'):
            sitemap_url = line.split(': ')[1]
            sitemaps.append(sitemap_url)
    return sitemaps

def load_url(url):
    response = requests.get(url)
    return response.text

def extract_urls(content):
    urls = []
    soup = BeautifulSoup(content, 'xml')
    loc_tags = soup.find_all('loc')
    for loc_tag in loc_tags:
        url = loc_tag.text
        urls.append(url)
    return urls

def is_sitemap_url(url):
    parsed_url = urlparse(url)
    return parsed_url.path.endswith('.xml')

def is_entry(url):
    parsed_url = urlparse(url)
    return '/entry/' in parsed_url.path

def check_duplicates(url, visited_urls):
    return url not in visited_urls

def store_unique_links(links, file):
    result = {
            'link': links
    }
    json.dump(result, file)
    file.write('\n')

def crawl(url, output_file_path='unique_links.json'):
    visited_urls = set()
    queue = [url + '/robots.txt']
    total_urls_processed = 0

    if os.path.exists(output_file_path):
        with open(output_file_path, 'r') as existingfile:
            for line in existingfile:
                data = json.loads(line)
                visited_urls.add(data['link'])

    print(f"Starting with {len(visited_urls)} urls")

    robots_txt_url = queue.pop(0)
    robots_txt = load_url(robots_txt_url)
    visited_urls.add(robots_txt_url)
    sitemaps = find_sitemaps(robots_txt)
    for sitemap_url in sitemaps:
        queue.append(sitemap_url)

    with open(output_file_path, 'a') as file:
        while queue:
            current_url = queue.pop(0)
            print(f"Processing URL: {current_url} queue size: {len(queue)} visited: {len(visited_urls)}")
            if current_url in visited_urls:
                continue
            visited_urls.add(current_url)
            total_urls_processed += 1

            if is_entry(current_url):
                store_unique_links(current_url, file)
                print(f"Stored URL: {current_url}")
                continue

            if not is_sitemap_url(current_url):
                with open('skipped.json', 'a') as skippedfile:
                    store_unique_links(current_url, skippedfile)
                    print(f"Skip URL: {current_url}")
                    continue

            # url is probably a sitemap
            url_content = load_url(current_url)
            urls = extract_urls(url_content)
            print(f"Found {len(urls)} URLs in sitemap {current_url}")

            for url in urls:
                queue.append(url)

            print(f"Progress: {total_urls_processed} URLs processed. Last URL: {current_url}")

        print(f"Total URLs processed: {total_urls_processed}")

# Start crawling from a given URL
crawl('https://huffpost.com')
