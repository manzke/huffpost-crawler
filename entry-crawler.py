import json
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timezone

# Function to extract full text and metadata from a news article URL
def extract_full_text_and_metadata(url):
    try:
        id = url.split('_')[-1]
        response = requests.get(url, allow_redirects=False)
        if response.status_code == 301 or response.status_code == 302:
            raise requests.RequestException("Redirect detected. Please check the URL.")
        response.raise_for_status()  # Check if the request was successful
        # print(f"Response code: {response.status_code}")
        # print(f"Response URL: {response.url}")
        # print(f"Response content: {response.content}")
        soup = BeautifulSoup(response.content, 'html.parser')

        # example url https://www.huffingtonpost.com/entry/the-limitless-potential-o_us_3526935

        # Extract metadata from the head tag
        metadata = {
            'title': '',
            'description': '',
            'language': soup.find('html')['lang'] if soup.find('html') and 'lang' in soup.find('html').attrs else '',
            'date-crawled': datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        }

        '''
        <script type="application/ld+json">{"@context":"http://schema.org","author":{"@context":"http://schema.org","@type":"Person","description":"Mollie Reilly is HuffPost's managing editor of breaking news. She is based in the San Francisco Bay Area. A graduate of Colgate University, she has worked at HuffPost since 2011 and specializes in breaking news, politics and California affairs. She can be reached by email at mollie.reilly@huffpost.com.","jobTitle":"Managing Editor, Breaking News, HuffPost","name":"Mollie Reilly","url":"https://www.huffpost.com/author/mollie-reilly"},"creator":{"@context":"http://schema.org","@type":"Person","description":"Mollie Reilly is HuffPost's managing editor of breaking news. She is based in the San Francisco Bay Area. A graduate of Colgate University, she has worked at HuffPost since 2011 and specializes in breaking news, politics and California affairs. She can be reached by email at mollie.reilly@huffpost.com.","jobTitle":"Managing Editor, Breaking News, HuffPost","name":"Mollie Reilly","url":"https://www.huffpost.com/author/mollie-reilly"},"dateCreated":"2017-08-10T21:39:43Z","dateModified":"2017-08-11T17:41:53Z","datePublished":"2017-08-10T21:39:43Z","description":"\"I greatly appreciate the fact that we’ve been able to cut our payroll.\"","headline":"Trump Thanks Putin For Kicking Out Diplomats: 'We're Going To Save A Lot Of Money'","image":{"@type":"ImageObject","url":"https://img.huffingtonpost.com/asset/598cc3852200002d001a569e.jpeg?cache=ecMa7byBqX&ops=1778_1000","width":1778,"height":1000},"inLanguage":"en-US","keywords":["donald-trump","international-news","barack-obama","russia","vladimir-putin","citizenship-in-the-united-states","us-russia-relations","sanctions","type: news"],"mainEntityOfPage":{"@type":"WebPage","@id":"https://www.huffpost.com/entry/trump-putin-diplomats_n_598cc320e4b090964295d76c"},"publisher":{"@type":"NewsMediaOrganization","name":"HuffPost","url":"https://www.huffpost.com","logo":{"@type":"ImageObject","url":"https://www.huffpost.com/static-assets/cambria/app/images/hp-amp.hash-3bfbf0a15bc4b64d5fbb.gif","width":600,"height":60}},"thumbnailUrl":"https://img.huffingtonpost.com/asset/598cc3852200002d001a569e.jpeg?cache=ecMa7byBqX&ops=200_150","url":"https://www.huffpost.com/entry/trump-putin-diplomats_n_598cc320e4b090964295d76c","@type":"NewsArticle","articleSection":"Politics","speakable":{"@type":"SpeakableSpecification","cssSelector":[".entry__header .headline",".entry__header .dek",".entry__content-list"]}}</script>
        <script type="application/ld+json">{"@context":"http://schema.org","author":{"@type":"Organization","name":"AP"},"creator":{"@type":"Organization","name":"AP"},"dateCreated":"2024-05-28T15:47:23Z","dateModified":"2024-05-28T17:37:43Z","datePublished":"2024-05-28T15:47:23Z","description":"U.S. District Judge Aileen Cannon said in her order that prosecutors didn’t give defense lawyers adequate time to discuss the request before it was filed Friday evening.","headline":"Judge Denies Request To Bar Trump Statements That Could Endanger Officers In Classified Docs Case","image":{"@type":"ImageObject","url":"https://img.huffingtonpost.com/asset/6655fbc22200003200e76dc6.jpeg?cache=dKWXaP8Akr&ops=1778_1000","width":1778,"height":1000},"inLanguage":"en-US","keywords":["donald-trump","politics","crime","mar-a-lago","type: news"],"mainEntityOfPage":{"@type":"WebPage","@id":"https://www.huffpost.com/entry/judge-denies-request-bar-trump-statements-that-could-endanger-officers-classified-docs-case_n_6655fae6e4b022987c31b354"},"publisher":{"@type":"NewsMediaOrganization","name":"HuffPost","url":"https://www.huffpost.com","logo":{"@type":"ImageObject","url":"https://www.huffpost.com/static-assets/cambria/app/images/hp-amp.hash-3bfbf0a15bc4b64d5fbb.gif","width":600,"height":60}},"thumbnailUrl":"https://img.huffingtonpost.com/asset/6655fbc22200003200e76dc6.jpeg?cache=dKWXaP8Akr&ops=200_150","url":"https://www.huffpost.com/entry/judge-denies-request-bar-trump-statements-that-could-endanger-officers-classified-docs-case_n_6655fae6e4b022987c31b354","@type":"NewsArticle","articleSection":"U.S. News","speakable":{"@type":"SpeakableSpecification","cssSelector":[".entry__header .headline",".entry__header .dek",".entry__content-list"]}}</script>
        '''
        ld_json_script = soup.find('script', type='application/ld+json')
        if ld_json_script:
            ld_json = json.loads(ld_json_script.string)
            
            metadata['description'] = ld_json['description'] if 'description' in ld_json else ''
            metadata['title'] = ld_json['headline'] if 'headline' in ld_json else ''
            metadata['keywords'] = ','.join(ld_json['keywords']) if 'keywords' in ld_json else ''
            metadata['section'] = ld_json['articleSection'] if 'articleSection' in ld_json else ''
            metadata['author'] = ld_json['author']['name'] if 'author' in ld_json and 'name' in ld_json['author'] else ''
            metadata['author-description'] = ld_json['author']['description'] if 'author' in ld_json and 'description' in ld_json['author'] else ''
            metadata['date-created'] = ld_json['dateCreated'] if 'dateCreated' in ld_json else ''
            metadata['date-modified'] = ld_json['dateModified'] if 'dateModified' in ld_json else ''
            metadata['date-published'] = ld_json['datePublished'] if 'datePublished' in ld_json else ''
            if not metadata['language'] or metadata['language'] == '':
                metadata['language'] = ld_json['inLanguage'] if 'inLanguage' in ld_json else ''
            
        '''
        <meta property="og:title" content="James Carville Says ‘Preachy Females’ Are Hurting Biden’s Appeal Among Dems">
        <meta property="og:description" content="“The message is too feminine,” the famed Democrat strategist said in a controversial interview.">
        <meta property="article:tag" content="Donald Trump,Joe Biden ,james carville">
        <meta property="article:section" content="Politics">
        <meta property="article:published_time" content="2024-03-25T11:00:57Z">
        <meta property="article:modified_time" content="2024-03-25T23:26:57Z">
        '''
        if not metadata['title'] or metadata['title'] == '':
            og_title_meta = soup.find('meta', attrs={'property': 'og:title'})
            if og_title_meta and 'content' in og_title_meta.attrs:
                metadata['title'] = og_title_meta['content']

        if not metadata['description'] or metadata['description'] == '':
            og_description_meta = soup.find('meta', attrs={'property': 'og:description'})
            if og_description_meta and 'content' in og_description_meta.attrs:
                metadata['description'] = og_description_meta['content']

        if not metadata['keywords'] or metadata['keywords'] == '':
            article_tag_meta = soup.find('meta', attrs={'property': 'article:tag'})
            if article_tag_meta and 'content' in article_tag_meta.attrs:
                metadata['keywords'] = article_tag_meta['content']
        
        if not metadata['section'] or metadata['section'] == '':
            article_section_meta = soup.find('meta', attrs={'property': 'article:section'})
            if article_section_meta and 'content' in article_section_meta.attrs:
                metadata['section'] = article_section_meta['content']
        
        if not metadata['date-published'] or metadata['date-published'] == '':
            article_published_time_meta = soup.find('meta', attrs={'property': 'article:published_time'})
            if article_published_time_meta and 'content' in article_published_time_meta.attrs:
                metadata['date-published'] = article_published_time_meta['content']

        if not metadata['date-modified'] or metadata['date-modified'] == '':
            article_modified_time_meta = soup.find('meta', attrs={'property': 'article:modified_time'})
            if article_modified_time_meta and 'content' in article_modified_time_meta.attrs:
                metadata['date-modified'] = article_modified_time_meta['content']
        
        if not metadata['description'] or metadata['description'] == '':
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
        
        return article_text.strip(), metadata, id
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        with open(error_file_path, 'a') as errorfile:
            result = {
                'id': id,
                'link': url,
                'message': f"Error fetching URL {url}: {e}"
            }
            json.dump(result, errorfile)
            errorfile.write('\n')
        return None, None, None    

# Read the JSON lines from the file
file_path = 'unique_links-2024-05-28.json'

# Open the output file in append mode
error_file_path = 'articles-errors-'+file_path
output_file_path = 'articles-'+file_path
with open(output_file_path, 'a') as outfile:
    with open(file_path, 'r') as file:
        json_lines = file.readlines()

    processed_links = set()
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r') as existingfile:
            for line in existingfile:
                data = json.loads(line)
                processed_links.add(data['link'])

    if os.path.exists(error_file_path):
        with open(error_file_path, 'r') as errorfile:
            for line in errorfile:
                data = json.loads(line)
                processed_links.add(data['link'])            

    filtered_json_lines = [line for line in json_lines if json.loads(line)['link'] not in processed_links]
    print(f"Filtered {len(json_lines) - len(filtered_json_lines)} duplicate articles")

    total_lines = len(filtered_json_lines)
    for i, line in enumerate(filtered_json_lines):
        data = json.loads(line)
        url = data['link']
        print(f"Processing URL: {url}")
        full_text, metadata, id = extract_full_text_and_metadata(url)
        
        if full_text:
            result = {
                'id': id,
                'link': url,
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
            json.dump(result, outfile)
            outfile.write('\n')
        
        # Print progress
        print(f"Processed {i + 1}/{total_lines} lines. Last {url}")

print(f"Articles have been saved to {output_file_path}")
