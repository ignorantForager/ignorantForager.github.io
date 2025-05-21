import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import random
import logging
import datetime
import os
import json

# --- Selenium Imports ---
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Use validated Firefox Headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

# Global Search/Scrape Settings
SEARCH_TERM = "internal hard drive" # Used by Amazon & Newegg
MAX_PAGES_PER_SITE = 4 # Used by Amazon (Newegg/SPD use different mechanisms)
MIN_DELAY_S = 4
MAX_DELAY_S = 8
REQUEST_TIMEOUT = 30 # Timeout for requests library

# --- Helper Functions ---

def parse_price(price_str):
    """Cleans price strings and returns a float."""
    if not price_str: return None
    try:
        price_str = re.sub(r'(?:USD|CAD|EUR|GBP|\$|£|€|,)', '', price_str)
        price_str = price_str.split('-')[0] # Handle price ranges
        price_str = re.sub(r'\s.*', '', price_str) # Remove text after first space
        return float(price_str.strip())
    except (ValueError, TypeError):
        logging.warning(f"Could not parse price: '{price_str}'")
        return None

def parse_capacity_tb(title):
    """Extracts capacity in TB from a string. Case-insensitive."""
    if not title: return None
    title_lower = title.lower()
    tb_match = re.search(r'(\d{1,3})\s*(?:tb|terabyte)\b', title_lower)
    if tb_match: return int(tb_match.group(1))
    gb_match = re.search(r'(\d{3,5})\s*(?:gb|gigabyte)\b', title_lower)
    if gb_match: return round(int(gb_match.group(1)) / 1000.0, 2)
    return None

def polite_delay():
    """Waits for a random time."""
    delay = random.uniform(MIN_DELAY_S, MAX_DELAY_S)
    logging.info(f"Waiting for {delay:.2f} seconds...")
    time.sleep(delay)

def create_html_link(title, url):
    """Creates an HTML anchor tag string."""
    if not url or not isinstance(url, str) or not url.startswith('http'):
        return title
    safe_title = title.replace('"', '"')
    return f'<a href="{url}" target="_blank" rel="noopener noreferrer" title="{safe_title}">{title}</a>'

# --- Scraping Functions ---

def scrape_amazon(search_term, max_pages=1):
    """Scrapes Amazon search results using requests."""
    logging.info(f"--- Scraping Amazon for '{search_term}' (Max Pages: {max_pages}) ---")
    results = []
    base_url = "https://www.amazon.com"
    search_url_template = base_url + "/s?k={query}&i=computers&rh=n%3A1254762011&ref=nb_sb_noss"

    session = requests.Session()
    session.headers.update(HEADERS)

    for page in range(1, max_pages + 1):
        query = '+'.join(search_term.split())
        url = f"{search_url_template.format(query=query)}&page={page}"
        logging.info(f"Requesting Amazon page {page}: {url}")
        response = None
        try:
            polite_delay()
            response = session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            if "captcha" in response.text.lower() or "robot check" in response.text.lower():
                 logging.warning(f"CAPTCHA detected on Amazon page {page}. Stopping Amazon scrape.")
                 break
        except requests.exceptions.Timeout:
            logging.error(f"Timeout error requesting Amazon page {page}: {url}")
            continue
        except requests.exceptions.HTTPError as e:
             logging.error(f"HTTP error requesting Amazon page {page}: {e.response.status_code} {e.response.reason} for URL: {url}")
             if e.response.status_code in [403, 404, 503]:
                 logging.error(f"Received {e.response.status_code}. Amazon might be blocking requests.")
                 if response: logging.debug(f"Response text (start): {response.text[:500]}")
                 break
             continue
        except requests.exceptions.RequestException as e:
            logging.error(f"Generic error requesting Amazon page {page}: {e}")
            continue

        soup = BeautifulSoup(response.content, 'lxml')
        items = soup.select('div[data-component-type="s-search-result"]')
        logging.debug(f"Found {len(items)} potential items on page {page} using primary selector.")
        if not items:
             items = soup.select('div.s-result-item[data-asin]')
             logging.debug(f"Primary selector failed. Found {len(items)} using fallback 'div.s-result-item[data-asin]'.")

        if not items and page == 1:
             logging.warning("No items found on Amazon page 1.")
             break
        if not items and page > 1:
             logging.info(f"No items found on Amazon page {page}. Assuming end of results.")
             break

        item_count_on_page = 0
        for item in items:
            sponsored_tag = item.select_one('span.s-label-popover-default, span.puis-sponsored-label-text')
            if sponsored_tag and ('Sponsored' in sponsored_tag.get_text(strip=True)): continue

            data = {'Retailer': 'Amazon'}
            title_container = item.select_one('div[data-cy="title-recipe"]')
            if not title_container: continue
            link_element = title_container.select_one('a.a-link-normal.s-underline-link-text.a-text-normal, a.a-link-normal')
            if not link_element: continue

            href = link_element.get('href')
            if href and href.startswith('/') and ('/dp/' in href or '/gp/product/' in href):
                data['URL'] = base_url + href
            else: continue

            title_h2 = link_element.select_one('h2.a-size-medium.a-color-base.a-text-normal, h2.a-size-base-plus.a-color-base.a-text-normal')
            if title_h2:
                title_span = title_h2.select_one('span')
                data['Title'] = title_span.get_text(strip=True) if title_span else title_h2.get_text(strip=True)
            else: data['Title'] = link_element.get_text(strip=True).strip()
            if not data.get('Title'): continue

            price_element = item.select_one('span.a-price > span.a-offscreen')
            price_str = None
            if price_element: price_str = price_element.get_text(strip=True)
            else:
                price_whole = item.select_one('span.a-price-whole')
                price_fraction = item.select_one('span.a-price-fraction')
                if price_whole and price_fraction: price_str = price_whole.get_text(strip=True) + price_fraction.get_text(strip=True)
                elif item.select_one('span.a-price'): price_str = item.select_one('span.a-price').get_text(strip=True)

            if price_str:
                data['Price'] = parse_price(price_str)
                if data['Price'] is None: continue
            else: continue

            data['Capacity (TB)'] = parse_capacity_tb(data.get('Title'))
            if not data['Capacity (TB)']: continue

            if data.get('Price') and data.get('Capacity (TB)') and data.get('URL') and data.get('Title'):
                results.append(data)
                item_count_on_page += 1

        logging.info(f"Successfully parsed {item_count_on_page} valid items from Amazon page {page}.")

    logging.info(f"Finished scraping Amazon. Found a total of {len(results)} valid items.")
    return results


def scrape_newegg(search_term, page_size=96):
    """Scrapes Newegg search results using Selenium by requesting a larger page size."""
    logging.info(f"--- Scraping Newegg for '{search_term}' using Selenium (PageSize={page_size}) ---")
    results = []
    base_url = "https://www.newegg.com"
    query = '+'.join(search_term.split())
    url = f"{base_url}/p/pl?d={query}&PageSize={page_size}"
    logging.info(f"Requesting Newegg page via Selenium: {url}")

    options = FirefoxOptions()
    if 'User-Agent' in HEADERS: options.add_argument(f'user-agent={HEADERS["User-Agent"]}')
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = None
    service = None
    try:
        os.environ['WDM_LOG_LEVEL'] = '0'
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        logging.info("Selenium Firefox driver initialized for Newegg.")

        page_load_successful = False
        block_found = False
        try:
            polite_delay()
            driver.get(url)
            time.sleep(3)

            current_page_source_lower = driver.page_source.lower()
            blocking_keywords = ["captcha", "are you a human", "verify your identity", "challenge", "access denied", "forbidden", "page not found", "something went wrong"]
            matched_keyword = None
            soup_for_check = BeautifulSoup(driver.page_source, 'lxml')
            for keyword in blocking_keywords:
                if keyword in current_page_source_lower:
                    h_tags = soup_for_check.select('h1, h2, h3, title')
                    found_in_header = any(keyword in tag.get_text(strip=True).lower() for tag in h_tags)
                    buttons = soup_for_check.select('button, input[type="submit"]')
                    found_in_button = any(keyword in btn.get_text(strip=True).lower() or keyword in btn.get('value', '').lower() for btn in buttons)
                    if found_in_header or found_in_button:
                        logging.warning(f"Blocking keyword '{keyword}' detected prominently on Newegg page.")
                        block_found = True
                        matched_keyword = keyword
                        break
                    else: logging.debug(f"Keyword '{keyword}' found in Newegg source, but not prominently.")

            if block_found:
                try:
                    blocked_html_path = os.path.join(os.getcwd(), f"newegg_blocked_{matched_keyword}_page_large.html")
                    with open(blocked_html_path, "w", encoding="utf-8") as f: f.write(driver.page_source)
                    logging.info(f"Saved HTML source of suspected blocked Newegg page to: {blocked_html_path}")
                except Exception as save_err: logging.error(f"Could not save blocked Newegg page HTML: {save_err}")
                logging.warning("Stopping Newegg scrape due to detected prominent block.")
            else:
                # Wait for items
                wait_timeout = 60
                item_selector = (By.CSS_SELECTOR, "div.item-cell")
                logging.debug(f"Waiting up to {wait_timeout}s for Newegg items '{item_selector[1]}'...")
                WebDriverWait(driver, wait_timeout).until(EC.presence_of_element_located(item_selector))
                logging.info("Newegg page loaded and item cells detected.")
                page_load_successful = True

        except TimeoutException:
            logging.warning(f"Timeout ({wait_timeout}s) waiting for item cells ('div.item-cell') on Newegg large page.")
            try:
                timeout_html_path = os.path.join(os.getcwd(), f"newegg_timeout_page_large.html")
                with open(timeout_html_path, "w", encoding="utf-8") as f: f.write(driver.page_source)
                logging.info(f"Saved HTML source of timed-out Newegg page to: {timeout_html_path}")
                page_text_lower = driver.page_source.lower()
                if "did not match any products" in page_text_lower or "we couldn't find any matches" in page_text_lower:
                     logging.warning(f"Newegg reported no results found for '{search_term}' after timeout.")
                else: logging.warning("Timeout occurred without finding 'no results' message.")
            except Exception as e: logging.error(f"Error checking/saving Newegg page source after timeout: {e}")
        except WebDriverException as e: logging.error(f"Selenium WebDriverException occurred loading Newegg page: {e}")
        except Exception as page_load_err: logging.error(f"Unexpected error during Newegg page load/block/wait phase: {page_load_err}", exc_info=True)

        if page_load_successful: # Proceed only if page loaded successfully and wasn't blocked
            try:
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'lxml')
                items = soup.select('div.item-cell')
                logging.info(f"Found {len(items)} potential items on Newegg page using 'div.item-cell'.")
                if not items: logging.warning("Items detected by wait, but not found by BeautifulSoup on Newegg page.")
                else:
                    item_count_on_page = 0
                    for item in items:
                        data = {'Retailer': 'Newegg'}
                        title_element = item.select_one('a.item-title')
                        if not title_element: continue
                        data['Title'] = title_element.get_text(strip=True)
                        href = title_element.get('href')
                        if href and href.startswith('http'): data['URL'] = href
                        else: continue

                        price_container = item.select_one('li.price-current')
                        price_str = None
                        if price_container:
                            price_strong = price_container.select_one('strong')
                            price_sup = price_container.select_one('sup')
                            if price_strong and price_sup: price_str = price_strong.get_text(strip=True) + price_sup.get_text(strip=True)
                            elif price_strong: price_str = price_strong.get_text(strip=True)
                            else: price_str = price_container.get_text(strip=True)
                            data['Price'] = parse_price(price_str)
                            if data['Price'] is None: continue
                        else: continue

                        data['Capacity (TB)'] = parse_capacity_tb(data.get('Title'))
                        if not data['Capacity (TB)']: continue

                        if data.get('Price') and data.get('Capacity (TB)') and data.get('URL') and data.get('Title'):
                            results.append(data)
                            item_count_on_page += 1
                    logging.info(f"Successfully parsed {item_count_on_page} valid items from Newegg page.")
            except Exception as parse_error: logging.error(f"Error parsing Newegg page content after loading: {parse_error}", exc_info=True)

    except WebDriverException as setup_error:
        logging.error(f"Failed to initialize or use Selenium WebDriver for Newegg: {setup_error}")
        return []
    except Exception as general_error:
        logging.error(f"An unexpected error occurred during Newegg Selenium scraping: {general_error}", exc_info=True)
        return []
    finally:
        if driver:
            try:
                driver.quit()
                logging.info("Selenium Firefox driver quit for Newegg.")
            except Exception as quit_error: logging.error(f"Error quitting Selenium driver for Newegg: {quit_error}")

    logging.info(f"Finished scraping Newegg using Selenium (PageSize={page_size}). Found a total of {len(results)} valid items.")
    return results


def scrape_serverpartdeals(url):
    """Scrapes ServerPartDeals collection page using Selenium."""
    logging.info(f"--- Scraping ServerPartDeals using Selenium ---")
    logging.info(f"Requesting SPD page via Selenium: {url}")
    results = []
    base_url = "https://serverpartdeals.com"

    options = FirefoxOptions()
    if 'User-Agent' in HEADERS: options.add_argument(f'user-agent={HEADERS["User-Agent"]}')
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = None
    service = None
    try:
        os.environ['WDM_LOG_LEVEL'] = '0'
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        logging.info("Selenium Firefox driver initialized for SPD.")

        page_load_successful = False
        block_found = False
        try:
            polite_delay()
            driver.get(url)
            static_sleep_duration = 7
            logging.debug(f"Static sleep for {static_sleep_duration}s after get() for initial JS load...")
            time.sleep(static_sleep_duration)

            # Block Check
            current_page_source_lower = driver.page_source.lower()
            blocking_keywords = ["captcha", "verify", "challenge", "access denied", "forbidden"]
            matched_keyword = None
            soup_for_check = BeautifulSoup(driver.page_source, 'lxml')
            for keyword in blocking_keywords:
                if keyword in current_page_source_lower:
                    h_tags = soup_for_check.select('h1, h2, h3, title')
                    found_in_header = any(keyword in tag.get_text(strip=True).lower() for tag in h_tags)
                    buttons = soup_for_check.select('button, input[type="submit"]')
                    found_in_button = any(keyword in btn.get_text(strip=True).lower() or keyword in btn.get('value', '').lower() for btn in buttons)
                    if found_in_header or found_in_button:
                        logging.warning(f"Blocking keyword '{keyword}' detected prominently on SPD page.")
                        block_found = True
                        matched_keyword = keyword
                        break
                    else: logging.debug(f"Keyword '{keyword}' found in SPD source, but not prominently.")

            if block_found:
                try:
                    blocked_html_path = os.path.join(os.getcwd(), f"spd_blocked_{matched_keyword}_page.html")
                    with open(blocked_html_path, "w", encoding="utf-8") as f: f.write(driver.page_source)
                    logging.info(f"Saved HTML source of suspected blocked SPD page to: {blocked_html_path}")
                except Exception as save_err: logging.error(f"Could not save blocked SPD page HTML: {save_err}")
                logging.warning("Stopping SPD scrape due to detected prominent block.")
            else:
                # Scroll and Wait for Inner Element Visibility
                try:
                    logging.debug("Scrolling down the SPD page...")
                    for _ in range(3):
                        driver.execute_script("window.scrollBy(0, document.body.scrollHeight * 0.6);")
                        time.sleep(1.5)

                    wait_timeout = 60
                    inner_item_selector_str = "a.boost-pfs-filter-product-item-title"
                    inner_item_selector = (By.CSS_SELECTOR, inner_item_selector_str)
                    logging.debug(f"Waiting up to {wait_timeout}s for VISIBILITY of SPD inner item element '{inner_item_selector[1]}'...")
                    WebDriverWait(driver, wait_timeout).until(EC.visibility_of_element_located(inner_item_selector))
                    logging.info(f"SPD Page processed and inner item elements ('{inner_item_selector_str}') are visible.")
                    page_load_successful = True

                except TimeoutException:
                    logging.warning(f"Timeout ({wait_timeout}s) waiting for VISIBILITY of inner item element ('{inner_item_selector_str}') on SPD page, even after scrolling.")
                    try:
                        timeout_html_path = os.path.join(os.getcwd(), f"spd_timeout_page_inner_visibility.html")
                        with open(timeout_html_path, "w", encoding="utf-8") as f: f.write(driver.page_source)
                        logging.info(f"Saved HTML source of timed-out (inner visibility) SPD page to: {timeout_html_path}")
                    except Exception as e: logging.error(f"Error checking/saving SPD page source after inner visibility timeout: {e}")
                except WebDriverException as e: logging.error(f"Selenium WebDriverException occurred during scroll/wait for SPD page: {e}")

        except Exception as page_load_err: logging.error(f"Unexpected error during SPD page load/block/wait phase: {page_load_err}", exc_info=True)

        if page_load_successful: # Proceed only if page loaded successfully and wasn't blocked
            try:
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'lxml')
                item_container_selector = "div.boost-pfs-filter-product-item-inner"
                items = soup.select(item_container_selector)
                logging.info(f"Found {len(items)} potential items on SPD page using '{item_container_selector}'.")
                if not items: logging.warning(f"Items visible by wait, but not found by BeautifulSoup('{item_container_selector}'). Parsing issue?")
                else:
                    item_count_on_page = 0
                    for item in items:
                        data = {'Retailer': 'ServerPartDeals'}
                        title_link_selector = "a.boost-pfs-filter-product-item-title"
                        title_element = item.select_one(title_link_selector)
                        if not title_element: continue
                        data['Title'] = title_element.get_text(strip=True)
                        href = title_element.get('href')
                        if href and href.startswith('/'): data['URL'] = base_url + href
                        else: continue

                        price_selector = "span.boost-pfs-filter-product-item-regular-price"
                        price_element = item.select_one(price_selector)
                        price_str = None
                        if price_element:
                            price_str = price_element.get_text(strip=True)
                            data['Price'] = parse_price(price_str)
                            if data['Price'] is None: continue
                        else: continue

                        data['Capacity (TB)'] = parse_capacity_tb(data.get('Title'))
                        if not data['Capacity (TB)']: continue

                        if data.get('Price') and data.get('Capacity (TB)') and data.get('URL') and data.get('Title'):
                            results.append(data)
                            item_count_on_page += 1
                    logging.info(f"Successfully parsed {item_count_on_page} valid items from SPD page.")
            except Exception as parse_error: logging.error(f"Error parsing SPD page content after loading: {parse_error}", exc_info=True)

    except WebDriverException as setup_error:
        logging.error(f"Failed to initialize or use Selenium WebDriver for SPD: {setup_error}")
        return []
    except Exception as general_error:
        logging.error(f"An unexpected error occurred during SPD Selenium scraping: {general_error}", exc_info=True)
        return []
    finally:
        if driver:
            try:
                driver.quit()
                logging.info("Selenium Firefox driver quit for SPD.")
            except Exception as quit_error: logging.error(f"Error quitting Selenium driver for SPD: {quit_error}")

    logging.info(f"Finished scraping ServerPartDeals using Selenium. Found a total of {len(results)} valid items.")
    return results


# --- Main Execution ---

if __name__ == "__main__":

    start_time = datetime.datetime.now()
    logging.info(f"Script started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    all_results = []
    scraper_status = {}

    # Define URLs/Search Terms
    amazon_search_term = SEARCH_TERM
    newegg_search_term = SEARCH_TERM
    serverpartdeals_url = "https://serverpartdeals.com/collections/manufacturer-recertified-drives"

    # --- Define Output Path for the static HTML report ---
    # Save to a 'pages' directory in the project root (or 'reports' as we discussed)
    # For GitHub Pages, if your repo is 'my-repo', files in 'pages/' are at 'my-repo/pages/'
    output_dir = 'pages'
    os.makedirs(output_dir, exist_ok=True)
    html_output_filename = os.path.join(output_dir, "hdd_prices_report.html")

    # --- Run Scrapers ---
    try:
        amazon_results = scrape_amazon(amazon_search_term, max_pages=MAX_PAGES_PER_SITE)
        all_results.extend(amazon_results)
        scraper_status['Amazon'] = {"status": "Success", "count": len(amazon_results), "details": f"{MAX_PAGES_PER_SITE} page(s)"}
    except Exception as e:
        logging.error(f"Amazon scraper failed critically: {e}", exc_info=True)
        scraper_status['Amazon'] = {"status": "Failed", "error": type(e).__name__}

    try:
        newegg_results = scrape_newegg(newegg_search_term, page_size=96)
        all_results.extend(newegg_results)
        scraper_status['Newegg'] = {"status": "Success", "count": len(newegg_results), "details": "1 large page"}
    except Exception as e:
        logging.error(f"Newegg scraper failed critically: {e}", exc_info=True)
        scraper_status['Newegg'] = {"status": "Failed", "error": type(e).__name__}

    try:
        spd_results = scrape_serverpartdeals(serverpartdeals_url)
        all_results.extend(spd_results)
        scraper_status['ServerPartDeals'] = {"status": "Success", "count": len(spd_results), "details": "1 page"}
    except Exception as e:
        logging.error(f"ServerPartDeals scraper failed critically: {e}", exc_info=True)
        scraper_status['ServerPartDeals'] = {"status": "Failed", "error": type(e).__name__}


    end_time = datetime.datetime.now()
    logging.info(f"All scraping finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        last_updated_str = end_time.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
    except ValueError:
        last_updated_str = end_time.strftime('%Y-%m-%d %H:%M:%S')

    # --- Prepare Status Message for HTML ---
    status_lines_html = []
    for site_name, site_data in scraper_status.items():
        if site_data['status'] == 'Success':
            details = f", {site_data.get('details', '')}" if site_data.get('details') else ''
            status_lines_html.append(f"<li>{site_name}: {site_data['status']} ({site_data.get('count', 0)} items{details})</li>")
        else:
            status_lines_html.append(f"<li><strong style='color: var(--error-text, #cc0000);'>{site_name}: {site_data['status']}</strong> (Error: {site_data.get('error', 'Unknown')})</li>")

    status_html_for_report = f"<ul>{''.join(status_lines_html)}</ul>"
    status_note_html = ""
    if 'Failed' in [s_data['status'] for s_data in scraper_status.values()]:
         status_note_html = "<p style='color: orange; text-align: center; font-size: 0.9em;'>Note: One or more scrapers failed. Results may be incomplete. Check console logs for details.</p>"

    # --- Process Combined Data for JavaScript and Initial HTML Table ---
    no_data_message_html = ""
    table_html_body_rows = "" # For initial render by Python
    js_data_json_string = "[]" # Default to empty array

    if not all_results:
        logging.warning("\nNo valid hard drive data found from ANY retailer after parsing.")
        no_data_message_html = f"""
        <div class="error-container">
            <p class="error">No valid hard drive data found from any retailer after parsing.</p>
            <p class="error-detail">Please check the script's console output for potential errors.</p>
        </div>
        """
    else:
        df = pd.DataFrame(all_results)
        df['Price per TB ($)'] = df.apply(
            lambda row: round(row['Price'] / row['Capacity (TB)'], 2) if pd.notna(row.get('Capacity (TB)')) and row['Capacity (TB)'] > 0 and pd.notna(row.get('Price')) else None,
            axis=1
        )
        df.dropna(subset=['Price per TB ($)', 'Capacity (TB)', 'Price', 'Title', 'URL', 'Retailer'], inplace=True)
        df_sorted = df.sort_values(by=['Price per TB ($)', 'Retailer'], ascending=True).reset_index(drop=True)

        if df_sorted.empty:
             no_data_message_html = f"""
             <div class="error-container">
                 <p class="error">No drives found after filtering and calculation.</p>
            </div>
            """
        else:
            js_data_df = df_sorted[['Retailer', 'Title', 'URL', 'Capacity (TB)', 'Price', 'Price per TB ($)']].copy()
            js_data_df.rename(columns={
                'Capacity (TB)': 'Capacity_TB',
                'Price per TB ($)': 'Price_per_TB'
            }, inplace=True)
            js_data_list = js_data_df.to_dict(orient='records')
            js_data_json_string = json.dumps(js_data_list)

            rows_html_list = []
            for index, row_data in df_sorted.iterrows():
                rows_html_list.append(f"""
                <tr>
                    <td class="text-center">{index + 1}</td>
                    <td>{row_data['Retailer']}</td>
                    <td>{create_html_link(row_data['Title'], row_data['URL'])}</td>
                    <td class="text-right">{row_data['Capacity (TB)']}</td>
                    <td class="text-right">${row_data['Price']:,.2f}</td>
                    <td class="text-right">${row_data['Price per TB ($)']:,.2f}</td>
                </tr>""")
            table_html_body_rows = "".join(rows_html_list)


    # --- Construct Full HTML Page ---
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HDD Price per TB (Sortable & Filterable)</title>
    <style>
        /* --- CSS Variables --- */
        :root {{
            --bg-color: #ffffff; --text-color: #333333; --link-color: #007bff;
            --border-color: #dddddd; --header-bg-color: #f8f8f8; --hover-bg-color: #f1f1f1;
            --subtle-text-color: #555555; --button-bg: #eee; --button-text: #333;
            --button-border: #ccc; --active-button-bg: #007bff; --active-button-text: white;
            --status-border: #ddd; --status-bg: #f9f9f9;
            --error-border: #e57373; --error-bg: #ffebee; --error-text: #c62828;
        }}
        body.dark-mode {{
            --bg-color: #121212; --text-color: #e0e0e0; --link-color: rgb(138, 180, 248); /* From user */
            --border-color: rgb(44, 45, 45); /* From user --main-border-color */
            --header-bg-color: #292929; /* From user --card-header-bg */
            --hover-bg-color: rgb(45, 56, 62); /* From user --tb-hover-bg */
            --subtle-text-color: #aaaaaa; --button-bg: #333; --button-text: #eee;
            --button-border: #555; --active-button-bg: rgb(138, 180, 248); --active-button-text: #121212;
            --status-border: rgb(44, 45, 45); --status-bg: #222;
            --error-border: #e57373; --error-bg: #4e3434; --error-text: #ffcdd2;
            /* Dark mode table specific (using user provided values) */
            --table-bg-dark-odd: rgb(31, 31, 34);    /* --tb-odd-bg */
            --table-bg-dark-even: rgb(27, 27, 30);   /* --tb-even-bg */
        }}
        /* --- General Styles --- */
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; background-color: var(--bg-color); color: var(--text-color); transition: background-color 0.3s, color 0.3s; display: flex; flex-direction: column; min-height: 100vh; }}
        .container {{ max-width: 1000px; margin: 0 auto; width: 100%; flex-grow: 1; }}
        header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 10px; margin-bottom: 20px; flex-wrap: wrap; }}
        .header-main-content {{ flex-grow: 1; text-align: center; }}
        h1 {{ margin: 0; font-size: 1.8em; }}
        .subtitle, .timestamp {{ color: var(--subtle-text-color); font-size: 0.9em; margin-top: 2px; width: 100%; }}
        .timestamp {{ margin-bottom: 0; }}
        .header-back-link {{ margin-right: auto; font-size: 0.9em; padding: 8px 0; }}
        .header-back-link a {{ color: var(--link-color); text-decoration: none; }}
        .header-back-link a:hover {{ text-decoration: underline; }}
        #themeToggle {{ padding: 8px 12px; background-color: var(--button-bg); color: var(--button-text); border: 1px solid var(--button-border); border-radius: 5px; cursor: pointer; font-size: 0.9em; transition: background-color 0.2s, border-color 0.2s; }}
        /* --- Status & Controls --- */
        .status-section, .controls-container {{ background-color: var(--status-bg); border: 1px solid var(--status-border); padding: 10px 15px; margin-bottom: 20px; border-radius: 5px; font-size: 0.9em; }}
        .status-section h3, .controls-container h4 {{ margin-top:0; margin-bottom: 8px; font-size: 1.1em; }}
        .status-section ul {{ margin: 0 0 5px 20px; padding: 0; list-style-type: disc; }}
        .status-section li {{ margin-bottom: 4px; }}
        .controls-container button {{ padding: 5px 10px; margin-right: 5px; margin-bottom: 5px; background-color: var(--button-bg); color: var(--button-text); border: 1px solid var(--button-border); border-radius: 3px; cursor: pointer; }}
        .controls-container button.active-sort {{ background-color: var(--active-button-bg); color: var(--active-button-text); border-color: var(--active-button-bg); }}
        .filter-group label {{ margin-right: 15px; display: inline-block; cursor:pointer; }}
        .filter-group input[type="checkbox"] {{ margin-right: 5px; vertical-align: middle; }}
        /* --- Table Styles --- */
        .table-responsive {{ overflow-x: auto; }}
        .results-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 0.95em; border: 1px solid var(--border-color); }}
        .results-table th, .results-table td {{ border: 1px solid var(--border-color); padding: 10px 8px; text-align: left; vertical-align: top; }}
        .results-table th {{ background-color: var(--header-bg-color); font-weight: bold; text-align: center; cursor: pointer; }}
        .results-table th:hover {{ background-color: var(--hover-bg-color); }}
        .results-table td:nth-child(1), .results-table th:nth-child(1) {{ width: 3em; text-align: center; }}
        .results-table td:nth-child(2), .results-table th:nth-child(2) {{ width: 100px; white-space: nowrap; }}
        .results-table td:nth-child(3), .results-table th:nth-child(3) {{ min-width: 200px; max-width: 350px; word-break: break-word; white-space: normal !important; }}
        .results-table td:nth-child(4), .results-table th:nth-child(4) {{ width: 80px; text-align: right; }}
        .results-table td:nth-child(5), .results-table th:nth-child(5) {{ width: 90px; text-align: right; }}
        .results-table td:nth-child(6), .results-table th:nth-child(6) {{ width: 80px; text-align: right; }}
        .results-table a {{ color: var(--link-color); text-decoration: none; }}
        .results-table a:hover {{ text-decoration: underline; }}
        .results-table tbody tr:hover > * {{ background-color: var(--hover-bg-color); }}
        /* Dark Mode Table Specifics */
        [data-theme="dark"] .results-table {{ color: var(--text-color); border-color: var(--border-color); }}
        [data-theme="dark"] .results-table th {{ background-color: var(--header-bg-color); border-color: var(--border-color); }}
        [data-theme="dark"] .results-table.table-striped > tbody > tr:nth-of-type(odd) > * {{ background-color: var(--table-bg-dark-odd); color: var(--text-color); }}
        [data-theme="dark"] .results-table.table-striped > tbody > tr:nth-of-type(even) > * {{ background-color: var(--table-bg-dark-even); color: var(--text-color); }}
        [data-theme="dark"] .results-table tbody tr:hover > * {{ background-color: var(--hover-bg-color); }}
        /* Error Message */
        .error-container {{ text-align: center; margin-top: 40px; padding: 20px; border: 1px solid var(--error-border); background-color: var(--error-bg); color: var(--error-text); border-radius: 5px; }}
        .error {{ font-weight: bold; margin-bottom: 5px; }}
        .error-detail {{ font-size: 0.9em; }}
        /* Responsive */
        @media (max-width: 768px) {{ body {{ padding: 10px; }} header {{ justify-content: center; }} #themeToggle {{ margin-top: 10px; margin-left:0; }} h1 {{ font-size: 1.5em; }} .results-table th, .results-table td {{ padding: 6px 4px; font-size: 0.85em; }} }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-back-link"><a href="/">← Back to Home</a></div>
            <div class="header-main-content">
                <h1>HDD Price per TB</h1>
                <p class="subtitle">Amazon, Newegg, ServerPartDeals</p>
                <p class="timestamp">Last Updated: {last_updated_str}</p>
            </div>
            <button id="themeToggle">Toggle Theme</button>
        </header>

        <div class="status-section">
             <h3>Scraper Status:</h3>
             {status_html_for_report}
        </div>

        <div class="controls-container">
            <h4>Sort By:</h4>
            <button class="sort-btn" data-sort-key="Retailer">Retailer</button>
            <button class="sort-btn" data-sort-key="Price">Price</button>
            <button class="sort-btn" data-sort-key="Capacity_TB">Size (TB)</button>
            <button class="sort-btn active-sort" data-sort-key="Price_per_TB">$/TB</button> <!-- Default sort -->
            <span id="currentSortIndicator" style="margin-left: 10px; font-style: italic; font-size: 0.9em;"></span>

            <h4 style="margin-top: 15px;">Filter by Retailer:</h4>
            <div id="retailerFilters" class="filter-group">
                <!-- Checkboxes will be populated by JavaScript -->
            </div>
        </div>

        {no_data_message_html}
        <div class="table-responsive">
            <table class="results-table table-striped">
                <thead>
                    <tr>
                        <th class="sort-btn" data-sort-key="#">#</th>
                        <th class="sort-btn" data-sort-key="Retailer">Retailer</th>
                        <th class="sort-btn" data-sort-key="Title">Product</th>
                        <th class="sort-btn" data-sort-key="Capacity_TB">Capacity (TB)</th>
                        <th class="sort-btn" data-sort-key="Price">Price ($)</th>
                        <th class="sort-btn" data-sort-key="Price_per_TB">$/TB</th>
                    </tr>
                </thead>
                <tbody>
                    {table_html_body_rows}
                </tbody>
            </table>
        </div>
        {status_note_html}
    </div>
    <script>
        const toggleButton = document.getElementById('themeToggle');
        const body = document.body;
        const currentTheme = localStorage.getItem('theme');
        const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
        function applyTheme(theme) {{
            if (theme === 'dark') {{ body.classList.add('dark-mode'); toggleButton.textContent = 'Switch to Light Mode'; localStorage.setItem('theme', 'dark'); }}
            else {{ body.classList.remove('dark-mode'); toggleButton.textContent = 'Switch to Dark Mode'; localStorage.setItem('theme', 'light'); }}
        }}
        if (currentTheme) {{ applyTheme(currentTheme); }}
        else if (prefersDarkScheme.matches) {{ applyTheme('dark'); }}
        else {{ applyTheme('light'); }}
        toggleButton.addEventListener('click', () => {{ applyTheme(body.classList.contains('dark-mode') ? 'light' : 'dark'); }});
        prefersDarkScheme.addEventListener('change', (e) => {{ if (!localStorage.getItem('theme')) {{ applyTheme(e.matches ? 'dark' : 'light'); }} }});
    </script>
    <script>
      // --- EMBED THE JAVASCRIPT FOR SORTING/FILTERING HERE ---
      // --- This is the full JS block from the previous correct answer ---
      const rawDriveData = {js_data_json_string};
      let currentSortKey = 'Price_per_TB';
      let currentSortDirection = 'asc';
      let currentFilters = {{ retailer: [] }}; // Initialize with empty array for retailers

      const tableBody = document.querySelector('.results-table tbody');
      const sortButtons = document.querySelectorAll('.sort-btn'); // Now includes THs
      const retailerFiltersContainer = document.getElementById('retailerFilters');
      const currentSortIndicator = document.getElementById('currentSortIndicator');

      function populateRetailerFilters() {{
          const retailers = [...new Set(rawDriveData.map(item => item.Retailer))].sort();
          retailers.forEach(retailer => {{
              const label = document.createElement('label');
              const checkbox = document.createElement('input');
              checkbox.type = 'checkbox';
              checkbox.value = retailer;
              checkbox.dataset.retailer = retailer; // For easier selection
              checkbox.checked = true;
              checkbox.addEventListener('change', applyFiltersAndRender);
              label.appendChild(checkbox);
              label.appendChild(document.createTextNode(` ${{retailer}}`));
              retailerFiltersContainer.appendChild(label);
          }});
          currentFilters.retailer = retailers; // Start with all selected
      }}

      function renderTable(dataToRender) {{
          tableBody.innerHTML = '';
          if (!dataToRender || dataToRender.length === 0) {{
              const row = tableBody.insertRow();
              const cell = row.insertCell();
              cell.colSpan = 6;
              cell.textContent = 'No matching drives found.';
              cell.style.textAlign = 'center';
              cell.style.padding = '20px';
              return;
          }}
          dataToRender.forEach((item, index) => {{
              const row = tableBody.insertRow();
              row.insertCell().textContent = index + 1;
              row.insertCell().textContent = item.Retailer;
              const productCell = row.insertCell();
              const link = document.createElement('a');
              link.href = item.URL;
              // Truncate title for display - adjust length as needed
              const maxTitleLength = 100;
              link.textContent = item.Title.length > maxTitleLength ? item.Title.substring(0, maxTitleLength - 3) + "..." : item.Title;
              link.title = item.Title; // Full title on hover
              link.target = '_blank';
              link.rel = 'noopener noreferrer';
              productCell.appendChild(link);
              row.insertCell().textContent = item.Capacity_TB;
              row.insertCell().textContent = `$${{parseFloat(item.Price).toFixed(2).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ",") }}`;
              row.insertCell().textContent = `$${{parseFloat(item.Price_per_TB).toFixed(2)}}`;

              row.cells[0].style.textAlign = 'center';
              row.cells[3].style.textAlign = 'right';
              row.cells[4].style.textAlign = 'right';
              row.cells[5].style.textAlign = 'right';
          }});
      }}

      function sortData(key, direction) {{
          // Get the currently displayed data (which might already be filtered)
          // Sorting should operate on the 'displayedData' array which is managed by applyFiltersAndRender
          // The global 'displayedData' will be sorted in place by this function.
          // It's reassigned in applyFilters() before sortData() is called.

          let dataToSort = JSON.parse(JSON.stringify(rawDriveData)); // Start with a fresh copy of raw data for filtering
          
          // Apply current filters to this fresh data
          if (currentFilters.retailer && currentFilters.retailer.length > 0) {{
              dataToSort = dataToSort.filter(item => currentFilters.retailer.includes(item.Retailer));
          }}
          // Add other filters here if they exist in currentFilters

          dataToSort.sort((a, b) => {{
              let valA = a[key];
              let valB = b[key];
              if (key === 'Price' || key === 'Capacity_TB' || key === 'Price_per_TB') {{
                  valA = parseFloat(valA);
                  valB = parseFloat(valB);
              }} else if (typeof valA === 'string') {{
                  valA = valA.toLowerCase();
                  valB = valB.toLowerCase();
              }}
              if (valA < valB) return direction === 'asc' ? -1 : 1;
              if (valA > valB) return direction === 'asc' ? 1 : -1;
              return 0;
          }});
          return dataToSort; // Return the sorted (and filtered) data
      }}
      
      function updateSortIndicator() {{
          const directionArrow = currentSortDirection === 'asc' ? '▲' : '▼';
          let columnText = currentSortKey;
          // Make column text more user-friendly
          const columnMap = {{
              'Retailer': 'Retailer', 'Title': 'Product', 'Capacity_TB': 'Size (TB)',
              'Price': 'Price', 'Price_per_TB': '$/TB', '#': '#'
          }};
          columnText = columnMap[currentSortKey] || currentSortKey;
          currentSortIndicator.textContent = `Sorted by: ${{columnText}} ${{directionArrow}}`;
          
          sortButtons.forEach(button => {{
              button.classList.remove('active-sort');
              if (button.dataset.sortKey === currentSortKey) {{
                  button.classList.add('active-sort');
              }}
          }});
      }}

      function applyFiltersAndRender() {{
          // 1. Get selected retailers
          const selectedRetailers = Array.from(retailerFiltersContainer.querySelectorAll('input[type="checkbox"]:checked'))
                                     .map(cb => cb.value);
          currentFilters.retailer = selectedRetailers;

          // 2. Filter raw data based on all current filters
          let filteredData = rawDriveData.filter(item => {{
              if (currentFilters.retailer && currentFilters.retailer.length > 0) {{
                  if (!currentFilters.retailer.includes(item.Retailer)) return false;
              }}
              // Add other filter conditions here
              return true;
          }});

          // 3. Sort the filtered data
          // (The sortData function was modified to take filteredData if needed, but here we sort 'in-place' the global filteredData)
           filteredData.sort((a, b) => {{
              let valA = a[currentSortKey];
              let valB = b[currentSortKey];
              if (currentSortKey === 'Price' || currentSortKey === 'Capacity_TB' || currentSortKey === 'Price_per_TB') {{
                  valA = parseFloat(valA);
                  valB = parseFloat(valB);
              }} else if (typeof valA === 'string') {{
                  valA = valA.toLowerCase();
                  valB = valB.toLowerCase();
              }}
              if (valA < valB) return currentSortDirection === 'asc' ? -1 : 1;
              if (valA > valB) return currentSortDirection === 'asc' ? 1 : -1;
              return 0;
          }});

          // 4. Render the table with this filtered and sorted data
          renderTable(filteredData);
          updateSortIndicator();
      }}

      sortButtons.forEach(button => {{
          button.addEventListener('click', (e) => {{
              // Use currentTarget if event bubbles from an inner element of TH
              const sortByKey = e.currentTarget.dataset.sortKey;
              if (sortByKey === '#') return; // Don't sort by rank

              if (currentSortKey === sortByKey) {{
                  currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
              }} else {{
                  currentSortKey = sortByKey;
                  currentSortDirection = 'asc';
              }}
              applyFiltersAndRender();
          }});
      }});

      // Initial Setup
      if (rawDriveData && rawDriveData.length > 0) {{
          populateRetailerFilters();
          applyFiltersAndRender(); // Initial render
      }} else {{
          renderTable([]); // Render "no data" message
          // Optionally disable controls if no data
          document.querySelector('.controls-container').style.display = 'none';
      }}
    </script>
</body>
</html>"""

    # --- Save HTML to File ---
    try:
        with open(html_output_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logging.info(f"\nHTML Results successfully saved to: {os.path.abspath(html_output_filename)}")
        print(f"\nHTML report generated: {os.path.abspath(html_output_filename)}")
    except Exception as e:
        logging.error(f"\nError saving HTML file '{html_output_filename}': {e}")
        print(f"\nError saving HTML file: {e}")
