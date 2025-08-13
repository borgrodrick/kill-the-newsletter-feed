import feedparser
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from urllib.parse import urljoin
import time

# --- CONFIGURATION ---
# 1. PASTE YOUR "KILL THE NEWSLETTER" RSS FEED URL HERE
SOURCE_RSS_URL = "https://kill-the-newsletter.com/feeds/zhiudoqjez0grmoizklb.xml"

# 2. CONFIGURE YOUR NEW FEED'S DETAILS
OUTPUT_FILE_NAME = "links_feed.xml"  # The name of the file to be generated
NEW_FEED_TITLE = "My Newsletter Links"
NEW_FEED_LINK = "http://localhost:8000" # A link to where you'll host the feed
NEW_FEED_DESCRIPTION = "A curated feed of links extracted from my newsletters."

# --- ADVANCED CONFIGURATION ---
REQUEST_TIMEOUT = 10 # seconds to wait for a website to respond
USER_AGENT = "NewsletterLinkExtractor/1.0" # How your script identifies itself

def get_link_title(url):
    """
    Visits a URL and attempts to extract the content of the <title> tag.
    Returns the title string or None if it fails.
    """
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, timeout=REQUEST_TIMEOUT, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            if soup.title and soup.title.string:
                return soup.title.string.strip()
        return None # Return None if no title or bad status code
    except requests.exceptions.RequestException as e:
        print(f"  -> Could not fetch {url}: {e}")
        return None

def generate_link_feed():
    """
    Main function to generate the feed.
    """
    print("Starting link extraction process...")

    # Initialize the new feed generator
    fg = FeedGenerator()
    fg.title(NEW_FEED_TITLE)
    fg.link(href=NEW_FEED_LINK, rel='alternate')
    fg.description(NEW_FEED_DESCRIPTION)

    # Fetch and parse the source "Kill the Newsletter" feed
    print(f"Fetching source feed from: {SOURCE_RSS_URL}")
    source_feed = feedparser.parse(SOURCE_RSS_URL)

    if source_feed.bozo:
        print(f"WARNING: Source feed may be malformed. Reason: {source_feed.bozo_exception}")

    # Set to keep track of links we've already added to avoid duplicates
    processed_links = set()

    # Iterate over each newsletter in the feed
    for entry in source_feed.entries:
        print(f"\nProcessing newsletter: '{entry.title}'")
        
        # The content is usually in 'content' or 'summary'
        if not hasattr(entry, 'content'):
            print("  -> No content found in this entry. Skipping.")
            continue
            
        html_content = entry.content[0].value
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all hyperlink tags
        links = soup.find_all('a', href=True)
        print(f"  -> Found {len(links)} links in the newsletter.")

        for link in links:
            url = link['href']
            
            # Make sure the URL is absolute
            url = urljoin(entry.link, url)

            # Skip mailto links and already processed links
            if url.startswith('mailto:') or url in processed_links:
                continue

            # Add to our set of processed links
            processed_links.add(url)
            
            print(f"  -> Crawling: {url}")
            title = get_link_title(url)
            
            # If we successfully got a title, add it to our new feed
            if title:
                fe = fg.add_entry()
                fe.title(title)
                fe.link(href=url)
                fe.description(f"Link found in newsletter: '{entry.title}'")
                fe.guid(url) # Use the URL as a unique identifier
                print(f"    ✅ Added to feed: '{title}'")
            else:
                print(f"    ❌ Could not get title for {url}. Skipping.")
            
            # Be a good internet citizen and wait a moment between requests
            time.sleep(0.5)

    # Generate the RSS file
    try:
        fg.rss_file(OUTPUT_FILE_NAME, pretty=True)
        print(f"\n✅ Success! New feed created at '{OUTPUT_FILE_NAME}'")
    except Exception as e:
        print(f"\n❌ Error generating RSS file: {e}")


if __name__ == "__main__":
    if "xxxxxxxx" in SOURCE_RSS_URL:
        print("ERROR: Please edit the script and replace the placeholder SOURCE_RSS_URL with your actual 'Kill the Newsletter' feed URL.")
    else:
        generate_link_feed()