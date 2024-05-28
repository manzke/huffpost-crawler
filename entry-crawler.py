import json
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timezone

# Function to extract full text and metadata from a news article URL
def extract_full_text_and_metadata(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract metadata from the head tag
        metadata = {
            'title': '',
            'description': '',
            'language': soup.find('html')['lang'] if soup.find('html') and 'lang' in soup.find('html').attrs else '',
            'crawled_at': datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        }

        '''
        <meta property="og:title" content="James Carville Says ‘Preachy Females’ Are Hurting Biden’s Appeal Among Dems">
        <meta property="og:description" content="“The message is too feminine,” the famed Democrat strategist said in a controversial interview.">
        <meta property="article:tag" content="Donald Trump,Joe Biden ,james carville">
        <meta property="article:section" content="Politics">
        <meta property="article:published_time" content="2024-03-25T11:00:57Z">
        <meta property="article:modified_time" content="2024-03-25T23:26:57Z">
        '''
        og_title_meta = soup.find('meta', attrs={'property': 'og:title'})
        if og_title_meta and 'content' in og_title_meta.attrs:
            metadata['title'] = og_title_meta['content']

        og_description_meta = soup.find('meta', attrs={'property': 'og:description'})
        if og_description_meta and 'content' in og_description_meta.attrs:
            metadata['description'] = og_description_meta['content']

        article_tag_meta = soup.find('meta', attrs={'property': 'article:tag'})
        if article_tag_meta and 'content' in article_tag_meta.attrs:
            metadata['tags'] = article_tag_meta['content']
        
        article_section_meta = soup.find('meta', attrs={'property': 'article:section'})
        if article_section_meta and 'content' in article_section_meta.attrs:
            metadata['section'] = article_section_meta['content']
        
        article_published_time_meta = soup.find('meta', attrs={'property': 'article:published_time'})
        if article_published_time_meta and 'content' in article_published_time_meta.attrs:
            metadata['published_time'] = article_published_time_meta['content']

        article_modified_time_meta = soup.find('meta', attrs={'property': 'article:modified_time'})
        if article_modified_time_meta and 'content' in article_modified_time_meta.attrs:
            metadata['modified_time'] = article_modified_time_meta['content']
        
        description_meta = soup.find('meta', attrs={'name': 'description'})
        if description_meta and 'content' in description_meta.attrs:
            metadata['description'] = description_meta['content']

        # Find the article tag and extract text from all tags within the article
        article = soup.find('article')
        if not article:
            print(f"No article tag found in {url}")
            return None, metadata
        
        article_text = ''
        for article in soup.find_all('article'):
            for div in article.find_all('div', {'id': 'support-huffpost-entry'}):
                div.decompose()  # Remove the div from the article
            for aside in article.find_all('aside', class_='entry__right-rail'):
                aside.decompose()  # Remove the aside from the article
            for paragraph in article.find_all('p'):
                if paragraph.get_text(strip=True):
                    article_text += paragraph.get_text(strip=True) + '\n'                
        
        return article_text.strip(), metadata
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None, None    

# Read the JSON lines from the file
file_path = 'unique_links-2024-05-28.json'

# Open the output file in append mode
output_file_path = 'articles-'+file_path+'.json'
with open(output_file_path, 'a') as outfile:
    with open(file_path, 'r') as file:
        json_lines = file.readlines()

    processed_links = set()
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r') as existingfile:
            for line in existingfile:
                data = json.loads(line)
                processed_links.add(data['link'])

    filtered_json_lines = [line for line in json_lines if json.loads(line)['link'] not in processed_links]
    print(f"Filtered {len(json_lines) - len(filtered_json_lines)} duplicate articles")

    total_lines = len(filtered_json_lines)
    for i, line in enumerate(filtered_json_lines):
        data = json.loads(line)
        url = data['link']

        full_text, metadata = extract_full_text_and_metadata(url)
        
        if full_text:
            result = {
                'link': url,
                'metadata': metadata,
                'content': full_text
            }
            json.dump(result, outfile)
            outfile.write('\n')
        
        # Print progress
        print(f"Processed {i + 1}/{total_lines} lines")

print(f"Articles have been saved to {output_file_path}")
