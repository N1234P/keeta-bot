from playwright.sync_api import sync_playwright
import re
import json
import threading
import time
from urllib.parse import urlparse

# Global cache to store metrics and reduce API calls
metrics_cache = {}
cache_expiry = 60  # Seconds to keep cache valid


def extract_tweet_id(url):
    """Extract the tweet ID from a Twitter/X URL"""
    if not url:
        return None

    # Parse the URL
    parsed = urlparse(url)

    # Ensure it's a Twitter/X URL
    if parsed.netloc not in ["twitter.com", "x.com"]:
        return None

    # Extract the tweet ID from the path
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) >= 3 and path_parts[1] == "status":
        return path_parts[2]

    return None


def get_tweet_metrics(twitter_id=None, url=None):
    """
    Get tweet metrics (likes, retweets, comments) using Playwright.
    This function runs in a separate thread to avoid blocking the main async loop.

    Args:
        twitter_id: The ID of the tweet (optional if url is provided)
        url: The full Twitter/X URL (optional if twitter_id is provided)

    Returns:
        tuple: (likes, retweets, comments)
    """
    # Extract tweet ID from URL if provided
    if url and not twitter_id:
        twitter_id = extract_tweet_id(url)

    if not twitter_id:
        return -1, -1, -1

    # Check cache first
    current_time = time.time()
    if twitter_id in metrics_cache:
        cache_time, metrics = metrics_cache[twitter_id]
        if current_time - cache_time < cache_expiry:
            return metrics

    # Create a separate thread to handle the browser operation
    metrics_result = [-1, -1, -1]  # Default values

    def playwright_thread():
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                try:
                    # Load the tweet page
                    page.goto(f"https://x.com/i/status/{twitter_id}", timeout=10000)

                    # Wait for tweet to load
                    page.wait_for_selector('[data-testid="tweet"]', timeout=10000)

                    # Extract metrics
                    metrics_result[0] = extract_count(page, "like")
                    metrics_result[1] = extract_count(page, "retweet")
                    metrics_result[2] = extract_count(page, "reply")

                except Exception as e:
                    print(f"Error extracting tweet metrics: {e}")
                finally:
                    browser.close()
        except Exception as e:
            print(f"Error in Playwright thread: {e}")

    # Start thread with a timeout
    thread = threading.Thread(target=playwright_thread)
    thread.daemon = True
    thread.start()
    thread.join(timeout=30)  # Timeout after 30 seconds

    # Update cache with the results
    metrics_cache[twitter_id] = (current_time, tuple(metrics_result))

    return tuple(metrics_result)


def extract_count(page, selector):
    """Extract and convert count from element"""
    try:
        text = page.locator(f'[data-testid="{selector}"]').first.text_content() or "0"
        # Convert K/M notation to numbers
        if "K" in text:
            return int(float(text.replace("K", "")) * 1000)
        elif "M" in text:
            return int(float(text.replace("M", "")) * 1000000)
        else:
            # Extract just numbers
            numbers = re.findall(r"\d+", text)
            return int(numbers[0]) if numbers else 0
    except:
        return 0


# Test function if this file is run directly
if __name__ == "__main__":
    # Example usage
    test_id = "191216sdf5266215096569"  # Example tweet ID
    likes, retweets, comments = get_tweet_metrics(twitter_id=test_id)
    print(f"Likes: {likes}, Retweets: {retweets}, Comments: {comments}")

    # Test URL extraction
    test_url = "https://x.com/username/status/1912165266215096569"
    extracted_id = extract_tweet_id(test_url)
    print(f"Extracted ID: {extracted_id}")
