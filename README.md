# huffpost-crawler
educational - how to use sitemap.xml for crawling a website (huffpost.com - could be any)

Every public website has (or should have) a sitemap.xml. The sitemap.xml allows robots like Google to find links, which should be crawled.

In the most cases the sitemaps can be found with just adding a /sitemap.xml to the domain or in bigger sites, check the robots.txt (ex. https://www.huffpost.com/robots.txt)

The robots.txt tells you where to find the sitemap.xml and if a robot is allowed to follow the links. A site can also manage to not get indexed, when it has the metatags for nofollow, noindex.

Your crawler should respect them to not read old content, privacy reasons, etc.

What does our crawler do?
- it loads the robots.txt
- detects the sitemaps
- loads every sitemap
- gets the urls from each sitemap
- which can be either another sitemap or a url
- we are loading each sitemap
- storing every url which is an entry as well as the skipped ones

This led to 1,121,569 unique links for new entries.

## robots.txt

A lot of LLM models have been trained on public data. To forbit it, pages has added

User-agent: GPTBot
Disallow: /

This tells the GPTBot to not crawl the site. Let's hope it complies with it.

Also take the Crawl-delay into account, which tells you how much time should be between every request to not get banned.

Example robots.txt from huffpost.com

```
# Cambria robots

User-agent: grapeshot
Disallow: /member
Disallow: /*?*err_code=404
Disallow: /search
Disallow: /search/?*

User-agent: *
Crawl-delay: 4
Disallow: /*?*page=
Disallow: /member
Disallow: /*?*err_code=404
Disallow: /search
Disallow: /search/?*
Disallow: /mapi/v4/*/user/*
Disallow: /embed

User-agent: Googlebot
Allow: /
Disallow: /*?*err_code=404
Disallow: /search
Disallow: /search/?*

User-agent: google-extended
Disallow: /

User-agent: GPTBot
Disallow: /

# archives
Sitemap: https://www.huffpost.com/sitemaps/sitemap-v1.xml
Sitemap: https://www.huffpost.com/sitemaps/sitemap-google-news.xml
Sitemap: https://www.huffpost.com/sitemaps/sitemap-google-video.xml
Sitemap: https://www.huffpost.com/sitemaps/sections.xml

# huffingtonpost.com archive sitemaps
Sitemap: https://www.huffpost.com/sitemaps-huffingtonpost/sitemap.xml
Sitemap: https://www.huffpost.com/sitemaps-huffingtonpost/sections.xml
``` 

## Inspired by
``` 
@article{misra2019sarcasm,
  title={Sarcasm Detection using Hybrid Neural Network},
  author={Misra, Rishabh and Arora, Prahal},
  journal={arXiv preprint arXiv:1908.07414},
  year={2019}
}

@book{misra2021sculpting,
  author = {Misra, Rishabh and Grover, Jigyasa},
  year = {2021},
  month = {01},
  pages = {},
  title = {Sculpting Data for ML: The first act of Machine Learning},
  isbn = {9798585463570}
}
``` 
