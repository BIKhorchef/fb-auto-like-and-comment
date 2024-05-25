import os
import json
import time
import random
import requests
import logging
from datetime import datetime
from threading import Thread

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementNotInteractableException,
    TimeoutException,
    StaleElementReferenceException,
)
from seleniumwire import webdriver

import pyotp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
TFA_SECRET = os.getenv('TFA_SECRET')
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
GROUP_LINKS = os.getenv('GROUP_LINKS')
MESSAGES = os.getenv('MESSAGES')

groups_links_list = GROUP_LINKS.split(',') if GROUP_LINKS else []
message = MESSAGES.split(',') if MESSAGES else []


comments = [
        "Looking so nice", "Hey! You look fantastic, dear.", "Awesome picture guys",
        "Nice place and nice picture", "You look elegant, man!", "How did you always manage to smile so well?",
        "Your face is glowing like a red rose", "This is your best picture man", "Wow, cute pie.",
        "Excellent, those eyes are always like a pearl.", "Your astonishing figure is one of the many things I like about you.",
        "You are incomparable.", "Your picture is the pride of Facebook.", "Perfection and professionalism are your game, and you are the master of it.",
        "If I continue praising you, I will end up worshipping you.", "Woohoo! So handsome, buddy.", "I love your sense of fashion.",
        "It speaks volumes of your beauty.", "Smart and sizzling, boy.", "Your beauty has captured my attention.",
        "Your photos are always excellent.", "I know this picture will get up to 1k likes.", "Super!", "Nice picture, bro.",
        "Innocent look!", "You are looking just like a rock star.", "Cool dude.",
        "Incredible height, fantastic curves, and that sumptuous dress girl...", "Oh Gosh! You are like an Angel from heaven."
    ]

# TOTP for 2FA
totp = pyotp.TOTP(TFA_SECRET)

# Suppress OpenXR errors by setting environment variables
os.environ['XR_RUNTIME_JSON'] = ''

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def load_profiles():
    try:
        with open('profiles.json', 'r') as file:
            config = json.load(file)
        return config['profiles']
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading profiles: {e}")
        return []

def setup_browser(profile):
    try:
        required_keys = ["binary_location", "chrome_user_data_dir", "profile_directory",
                         "executable_path", "proxy_host", "proxy_port", "proxy_user", "proxy_pass",
                         "expected_country", "expected_city"]
        for key in required_keys:
            if key not in profile:
                raise KeyError(key)

        chrome_options = ChromeOptions()
        chrome_options.binary_location = profile["binary_location"]
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f'--user-data-dir={profile["chrome_user_data_dir"]}')
        chrome_options.add_argument(f'--profile-directory={profile["profile_directory"]}')
        chrome_options.add_argument("--enable-chrome-browser-cloud-management")
        chrome_options.add_argument("--disable-proxy-certificate-handler")
        chrome_options.add_argument("--no-sandbox")  # Disabling sandbox to avoid file system permission issues
        chrome_options.add_argument("--disable-dev-shm-usage")  # Disabling shared memory usage to avoid some crashes
        chrome_options.add_argument("--disable-software-rasterizer")  # Disabling software rasterizer to improve performance

        # Path to the Selenium Wire CA certificate
        selenium_wire_ca_cert_path = r'.menv\Lib\site-packages\seleniumwire\ca.crt'
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--allow-insecure-localhost')
        chrome_options.add_argument('--ignore-urlfetcher-cert-requests')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument(f'--ssl-client-certificate-data={selenium_wire_ca_cert_path}')

        proxy_options = {
            'proxy': {
                'http': f'http://{profile["proxy_user"]}:{profile["proxy_pass"]}@{profile["proxy_host"]}:{profile["proxy_port"]}',
                'https': f'https://{profile["proxy_user"]}:{profile["proxy_pass"]}@{profile["proxy_host"]}:{profile["proxy_port"]}',
                'no_proxy': 'localhost,127.0.0.1'
            }
        }

        service = ChromeService(executable_path=profile["executable_path"])
        browser = webdriver.Chrome(service=service, seleniumwire_options=proxy_options, options=chrome_options)
        browser.get('https://ipinfo.io/json')

        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'pre'))
        )

        ip_info = json.loads(browser.find_element(By.TAG_NAME, 'pre').text)
        country = ip_info.get('country')
        city = ip_info.get('city')

        expected_country = profile.get("expected_country", "")
        expected_city = profile.get("expected_city", "")

        if country != expected_country:
            print(f"{bcolors.FAIL}Proxy is not working as expected. Country: {country}, City: {city}{bcolors.ENDC}")
            logging.warning(f"Proxy is not working as expected. Country: {country}, City: {city}")
            browser.quit()
            return None

        print(f"{bcolors.OKGREEN}Proxy is working correctly. Country: {country}, City: {city}{bcolors.ENDC}")
        logging.info(f"Proxy is working correctly. Country: {country}, City: {city}")
        browser.get("https://www.facebook.com/")

    except (TimeoutException, KeyError, Exception) as e:
        print(f"{bcolors.FAIL}Error setting up browser: {e}{bcolors.ENDC}")
        logging.error(f"Error setting up browser: {e}")
        return None

    return browser

def login(browser):
    """Handles the login process, including 2FA, by simulating human-like typing."""
    email_input = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="email"]'))
    )
    email_input.click()
    human_type(email_input, USER)  # Use the human_type function for typing the username

    password_input = browser.find_element(By.XPATH, '//*[@id="pass"]')
    password_input.click()
    human_type(password_input, PASSWORD)  # Use the human_type function for typing the password

    login_button = browser.find_element(By.XPATH, '//*[@id="loginbutton"]')
    login_button.click()

    otp_input = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="approvals_code"]'))
    )
    otp_code = totp.now()  # Generate the current OTP
    human_type(otp_input, otp_code)  # Type the OTP code with simulated human typing

    otp_submit_button = browser.find_element(By.XPATH, '//*[@id="checkpointSubmitButton"]')
    otp_submit_button.click()

def handle_checkpoint(browser):
    """Checks and handles the Facebook checkpoint if present."""
    time.sleep(5)  # Better replaced by WebDriverWait for specific page element or condition
    current_url = browser.current_url
    if current_url == "https://www.facebook.com/checkpoint/?next":
        try:
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="checkpointSubmitButton"]'))
            )
            remember_browser_button = browser.find_element(By.XPATH, '//*[@id="checkpointSubmitButton"]')
            remember_browser_button.click()
            logging.info("Action performed on the checkpoint page.")
        except Exception as e:
            logging.warning("Failed to perform action on the checkpoint page: %s", e)
    else:
        logging.info("No action required for the current URL.")

def post_to_groups(browser):
    """Posts a message with images to specified Facebook groups."""

    for group_link in groups_links_list:
        try:
            browser.get(group_link)
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div[4]/div/div/div[2]/div/div/div[1]/div[1]/div/div/div/div[1]/div/div[1]'))
            ).click()
            
            # Find the input box and enter text
            input_box = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[1]/div/div[4]/div/div/div[1]/div/div[2]/div/div/div/div/div[1]/form/div/div[1]/div/div/div[1]/div/div[2]/div[1]/div[1]/div[1]/div[1]/div/div/div/div/div[2]/div/div/div/div"))
            )
            time.sleep(5)
            random_message = random.choice(message)  # Choose a random message
            ActionChains(browser).move_to_element(input_box).click().send_keys(random_message).perform()

            # Post the message
            post_button = WebDriverWait(browser, 20).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div[1]/div/div[4]/div/div/div[1]/div/div[2]/div/div/div/div/div[1]/form/div/div[1]/div/div/div[1]/div/div[3]/div[3]/div/div"))
            )
            time.sleep(5)
            post_button.click()
            logging.info(f"Successfully posted to {group_link}: {random_message}")
            time.sleep(10)  # Wait for post to complete
            browser.get('https://www.facebook.com')
        except Exception as e:
            # browser.save_screenshot('error.png')  # Save a screenshot on error
            logging.error(f"Failed to post to {group_link}: {e}")

def human_type(element: WebElement, text: str, min_delay: float = 0.05, max_delay: float = 0.2):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))

def like_posts(browser, num_likes=1):
    print(bcolors.OKBLUE + "ACTION: Liking posts." + bcolors.ENDC)
    start_time = time.time()
    posts_liked = 0
    total_duration = 300

    logging.info("ACTION STARTED: Starting the like posts operation")

    try:
        while posts_liked < num_likes and (time.time() - start_time) < total_duration:
            logging.info("Scrolling to load more posts.")
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.randint(5, 10))

            like_buttons = WebDriverWait(browser, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, '//div[@aria-label="Like"]'))
            )

            i = 0
            while i < len(like_buttons):
                like_button = like_buttons[i]
                if like_button.is_displayed() and like_button.is_enabled():
                    try:
                        time.sleep(random.randint(10, 20))
                        ActionChains(browser).move_to_element(like_button).click().perform()
                        posts_liked += 1
                        logging.info(f"Successfully liked post {posts_liked}.")
                        if posts_liked >= num_likes:
                            logging.info("Reached the desired number of likes for this session.")
                            break
                        time.sleep(random.randint(2, 5))
                    except Exception as e:
                        logging.warning(f"Failed to like a post at index {i}: {e}")
                        continue
                skip_count = random.randint(3, 6)
                i += skip_count
                logging.info(f"Skipping {skip_count} posts after liking one.")
    except Exception as e:
        logging.error(f"Failed to like posts during session: {e}")
    finally:
        logging.info("ACTION COMPLETED: Like posts operation completed.")

def publish_post(browser):
    try:
        whats_on_your_mind = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '//span[contains(text(),"What\'s on your mind")]'))
        )
        whats_on_your_mind.click()
        time.sleep(2)

        create_post_text = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[contains(@aria-label, "Create a post")]'))
        )
        actions = ActionChains(browser)
        actions.move_to_element(create_post_text).click().send_keys(random.choice(message)).perform()
        time.sleep(5)

        publish_btn_post = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Post"]'))
        )
        publish_btn_post.click()

        logging.info("Post published successfully.")
    except Exception as e:
        logging.error(f"Failed to publish post: {e}")

def scroll_page(browser, scroll_pause_time=1.0, max_scroll_iterations=15):
    step_size = browser.execute_script("return window.innerHeight;") // 4

    for _ in range(max_scroll_iterations):
        scroll_distance = step_size + random.randint(-step_size // 2, step_size // 2)
        browser.execute_script(f"window.scrollBy(0, {scroll_distance});")
        time.sleep(random.uniform(scroll_pause_time, scroll_pause_time * 2))

        if random.random() < 0.1:
            scroll_up_distance = random.randint(step_size // 2, step_size)
            browser.execute_script(f"window.scrollBy(0, -{scroll_up_distance});")
            time.sleep(random.uniform(0.5, 1.0))

        new_height = browser.execute_script("return document.body.scrollHeight")
        scrolled_height = browser.execute_script("return window.pageYOffset;")
        remaining_height = new_height - scrolled_height - step_size * 3

        if remaining_height < browser.execute_script("return window.innerHeight;"):
            break

        step_size = min(step_size + 50, new_height // 3)

    final_scroll = random.randint(-step_size // 2, step_size // 2)
    browser.execute_script(f"window.scrollBy(0, {final_scroll});")
    time.sleep(0.5)

def scroll_down(browser):
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

def comment_on_posts(browser):
    logging.info("ACTION STARTED: Commenting on posts")
    scroll_page(browser)
    try:
        chosen_comment = random.choice(comments)
        comment_button = WebDriverWait(browser, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@aria-label="Leave a comment"]'))
        )
        time.sleep(2)
        try:
            comment_button.click()
        except Exception as e:
            browser.execute_script("arguments[0].click();", comment_button)

        time.sleep(5)
        input_cmnt = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@aria-label="Write a comment…"]'))
        )
        input_cmnt.click()
        time.sleep(5)
        human_type(input_cmnt, chosen_comment)
        time.sleep(5)
        input_cmnt.send_keys(Keys.ENTER)
        time.sleep(5)
        logging.info(f"Commented on post successfully, comment: {chosen_comment}")

        try:
            close_comment_button = browser.find_element(By.XPATH, '//*[@aria-label="Close"]')
            if close_comment_button.is_displayed():
                close_comment_button.click()
        except NoSuchElementException:
            logging.info("No close comment button found, continuing without closing.")

        time.sleep(5)
        scroll_down(browser)
        logging.info("ACTION COMPLETED: Finished commenting on posts.")
    except NoSuchElementException:
        logging.error("Comment button or input box not found.")
    except ElementNotInteractableException:
        logging.error("Element not interactable at the time of interaction.")
    except TimeoutException:
        logging.error("Timeout while waiting for the elements.")
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")

def share_post(browser, num_shares=1, skip_posts=4):
    logging.info("ACTION STARTED: Sharing posts")
    start_time = time.time()
    posts_shared = 0
    shared_indices = set()

    while posts_shared < num_shares and (time.time() - start_time) < 300:
        scroll_down(browser)
        time.sleep(10)

        share_buttons = WebDriverWait(browser, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[@aria-label="Send this to friends or post it on your profile."]'))
        )

        for i in range(len(share_buttons)):
            if i % (skip_posts + 1) == 0 and i not in shared_indices:
                try:
                    share_button = share_buttons[i]
                    if share_button.is_displayed() and share_button.is_enabled():
                        ActionChains(browser).move_to_element(share_button).click().perform()
                        time.sleep(5)

                        share_now_button = WebDriverWait(browser, 10).until(
                            EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Share now"]'))
                        )
                        share_now_button.click()
                        time.sleep(5)

                        posts_shared += 1
                        shared_indices.add(i)
                        logging.info(f"Successfully shared post {posts_shared}")
                        if posts_shared >= num_shares:
                            logging.info("ACTION COMPLETED: All requested posts have been shared successfully.")
                            return
                        time.sleep(60)
                except Exception as e:
                    logging.warning(f"Failed to share a post: {e}")
                    continue

    if posts_shared < num_shares:
        logging.error("Failed to complete sharing due to some issues.")
    else:
        logging.info("ACTION COMPLETED: All requested posts have been shared successfully.")

def invite_friends(browser, num_invitations=1):
    try:
        logging.info("ACTION STARTED: Inviting friends")
        print(bcolors.OKBLUE + "ACTION: Inviting friends." + bcolors.ENDC)
        browser.get('https://web.facebook.com/friends/suggestions')
        time.sleep(5)

        buttons = WebDriverWait(browser, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[starts-with(@aria-label, 'Add Friend')]"))
        )

        invitations_sent = 0
        i = 0
        while invitations_sent < num_invitations and i < len(buttons):
            try:
                button = buttons[i]
                if button.is_displayed():
                    button.click()
                    time.sleep(5)
                    logging.info(f"Invited friend {invitations_sent + 1} successfully")
                    invitations_sent += 1
                i += 3
            except StaleElementReferenceException:
                logging.warning("Stale Element Reference detected, refetching elements.")
                buttons = WebDriverWait(browser, 20).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[starts-with(@aria-label, 'Add Friend')]"))
                )
                continue
            except Exception as e:
                logging.error(f"Error when trying to invite: {e}")
                i += 1

        logging.info("ACTION COMPLETED: Invited friends successfully.")
        browser.get('https://web.facebook.com')
    except NoSuchElementException:
        logging.error("Invite button not found.")
    except ElementNotInteractableException:
        logging.error("Element not interactable at the time of interaction.")
    except TimeoutException:
        logging.error("Timeout while waiting for the elements.")
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")

def infinite_scroll_with_refresh(browser, timeout=1000):
    logging.info("ACTION STARTED: Starting Infinite scroll with refresh")
    print(bcolors.OKBLUE + "ACTION: Starting Infinite scroll with refresh." + bcolors.ENDC)
    old_height = browser.execute_script("return document.body.scrollHeight")
    start_time = time.time()

    while time.time() - start_time < timeout:
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        logging.info("Scrolled to bottom of the page.")
        time.sleep(10)
        
        new_height = browser.execute_script("return document.body.scrollHeight")
        if new_height == old_height:
            logging.info("No new data loaded; refreshing page...")
            browser.refresh()
            time.sleep(10)
        else:
            old_height = new_height
            logging.info("New data loaded, updated scroll height.")
        time.sleep(random.uniform(2, 5))

    logging.info("ACTION COMPLETED: Finished scrolling or timeout reached.")

def telegram_bot_sendtext(bot_message):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_message = f"{current_time} - {bot_message}"
    send_text = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&parse_mode=Markdown&text={full_message}'
    response = requests.get(send_text)
    return response.json()

def telegram_bot_send_document(file_path):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendDocument'
    with open(file_path, 'rb') as document:
        files = {'document': document}
        data = {'chat_id': CHAT_ID}
        response = requests.post(url, files=files, data=data)
    return response.json()

def refresh_page(browser):
    browser.refresh()
    time.sleep(5)  # Add a small delay to allow the page to fully refresh

def is_browser_alive(browser):
    try:
        return browser.current_url is not None
    except:
        return False

def main(profile): 
    logging.basicConfig(filename=f'fbwarming_{profile["user"]}.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    browser = setup_browser(profile)
    if browser is None:
        logging.error("Proxy is not configured properly. Exiting script.")
        return  # Exit the function if proxy configuration is not available

    actions = [
        like_posts, infinite_scroll_with_refresh, comment_on_posts, infinite_scroll_with_refresh, invite_friends, infinite_scroll_with_refresh,
        like_posts, infinite_scroll_with_refresh, comment_on_posts, infinite_scroll_with_refresh, invite_friends, infinite_scroll_with_refresh,
        like_posts, infinite_scroll_with_refresh, comment_on_posts, infinite_scroll_with_refresh, invite_friends, infinite_scroll_with_refresh,
        infinite_scroll_with_refresh, invite_friends,
        infinite_scroll_with_refresh, invite_friends,
        infinite_scroll_with_refresh, invite_friends,
        infinite_scroll_with_refresh, invite_friends,
        infinite_scroll_with_refresh, invite_friends,
        infinite_scroll_with_refresh, invite_friends,
        infinite_scroll_with_refresh, invite_friends,
               ]
    num_actions = len(actions)
    interval = 24 * 60 * 60 / num_actions  # Total seconds in 24 hours divided by the number of actions

    cycle_count = 0
    while True:
        logging.info(f"Starting action cycle {cycle_count + 1}")
        telegram_bot_sendtext("Start warming")
        if not is_browser_alive(browser):
            logging.error("Browser window is closed. Exiting script.")
            break  # Exit the loop if the browser window is closed
        start_cycle = time.time()
        for action in actions:
            action_name = action.__name__
            try:
                if not is_browser_alive(browser):
                    logging.error("Browser window is closed. Exiting script.")
                    break  # Exit the loop if the browser window is closed
                refresh_page(browser)  # Refresh the page before each action starts
                action_start = time.time()
                action(browser)
                action_duration = time.time() - action_start
                sleep_time = max(0, interval - action_duration)
                logging.info(f"Sleeping for {sleep_time} seconds before next action.")
                time.sleep(sleep_time)
            except Exception as e:
                logging.error(f"An error occurred during {action_name}: {e}")
                time.sleep(interval)  # Ensure to wait the full interval even if there's an error
        cycle_duration = time.time() - start_cycle
        if cycle_duration < 24 * 60 * 60:
            time.sleep(24 * 60 * 60 - cycle_duration)  # Ensure the cycle takes exactly 24 hours
        cycle_count += 1
        logging.info(f"Completed action cycle {cycle_count}. Waiting to start next cycle.")
        telegram_bot_send_document(f'fbwarming_{profile["user"]}.log')
        telegram_bot_sendtext("Finish warming")

if __name__ == "__main__":
    
    profiles = load_profiles()  
    for profile in profiles:
        main(profile)