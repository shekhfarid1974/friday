# brain.py
import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import random
# Import the speak function from utils
from utils import speak

# -----------------------------
# Google Search Functionality
# -----------------------------

def search_google_simple(query, num_results=3):
    """
    Attempts to fetch search results from Google.
    Note: This is basic and might be fragile/blocked.
    Consider using a proper Search API for production.
    """
    headers = {
        # Mimic a real browser request
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    # Encode the query for URL
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded_query}&num={num_results}"

    try:
        print(f"🧠 [Brain] Searching Google for: '{query}'")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes

        soup = BeautifulSoup(response.text, 'html.parser')

        # --- Attempt to extract snippets ---
        # Google's HTML structure changes frequently.
        # These selectors are examples and might need updating.

        # Method 1: Look for spans with class 'hgKElc' (common for descriptions)
        potential_snippets = soup.find_all('span', class_='hgKElc')
        for snippet in potential_snippets:
             snippet_text = snippet.get_text()
             if snippet_text and len(snippet_text.strip()) > 10:
                 return snippet_text.strip()

        # Method 2: Look for divs with class 'VwiC3b' (another common class)
        potential_divs = soup.find_all('div', class_='VwiC3b')
        for div in potential_divs:
            # Often the text is directly inside, or in nested spans
            snippet_text = div.get_text(separator=' ', strip=True)
            if snippet_text and len(snippet_text) > 10: # Basic check for meaningful content
               return snippet_text

        # Method 3: Fallback - Look for the first <p> tag within search result divs (class 'g')
        result_divs = soup.find_all('div', class_='g')
        for div in result_divs[:3]: # Check first few results
             p_tag = div.find('p')
             if p_tag:
                 snippet_text = p_tag.get_text()
                 if snippet_text:
                     return snippet_text.strip()

        # Method 4: Look for divs with class 'MgUUmf' (seen in 'People also ask' sometimes, might have text)
        # This is less reliable but another potential source.
        potential_divs_2 = soup.find_all('div', class_='MgUUmf')
        for div in potential_divs_2:
            snippet_text = div.get_text(separator=' ', strip=True)
            if snippet_text and len(snippet_text) > 10:
               return snippet_text


        print("⚠️ [Brain] Could not extract a clear snippet from Google results.")
        return "I found results, but couldn't extract the main information snippet clearly."

    except requests.exceptions.RequestException as e:
        print(f"❌ [Brain] Error fetching results from Google: {e}")
        return "I couldn't connect to Google right now."
    except Exception as e:
         print(f"❌ [Brain] An unexpected error occurred during search: {e}")
         # Optional: Print part of the error for debugging (be careful with sensitive info)
         # print(f"Error details: {str(e)[:100]}...")
         return "I encountered an error while searching."

def search_google_and_respond(query):
    """
    Main function to search Google and respond via speak/print.
    """
    if not query or query.lower() in ["none", ""]:
        print("[Brain] No query provided for search.")
        speak("I didn't catch what you wanted me to search for.")
        return

    # Optional: Add a small delay to avoid being too aggressive
    # time.sleep(0.5)

    result_snippet = search_google_simple(query)

    print(f"🔎 [Brain] Google Result Snippet: {result_snippet}")

    if result_snippet:
        speak(result_snippet)
    else:
        speak("I couldn't find specific information for that query.")

# --- Example usage (if run directly) ---
# if __name__ == "__main__":
#     # For testing brain.py independently
#     test_query = "current weather in Tokyo"
#     search_google_and_respond(test_query)
#     # Keep the script alive briefly to hear the response
#     import time
#     time.sleep(5)
