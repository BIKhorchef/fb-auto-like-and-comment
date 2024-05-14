from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys 
import pyotp
import os
from dotenv import load_dotenv
import logging
import time
import random
import requests
from datetime import datetime
from threading import Thread
import json


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

# Load environment variables
load_dotenv()
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
TFA_SECRET = os.getenv('TFA_SECRET')
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
# Fetch and parse the group links
GROUP_LINKS = os.getenv('GROUP_LINKS')
if GROUP_LINKS:
    groups_links_list = GROUP_LINKS.split(',')
else:
    groups_links_list = []

# Fetch and parse the messages
MESSAGES = os.getenv('MESSAGES')
if MESSAGES:
    message = MESSAGES.split(',')
else:
    message = []
    
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

# Create TOTP object for 2FA
totp = pyotp.TOTP(TFA_SECRET)

def load_profiles():
    with open('profiles.json', 'r') as file:
        config = json.load(file)
    return config['profiles']

def setup_browser():
    """Initializes and returns a Chrome WebDriver using a specific Chrome profile and custom driver path."""
    
    chrome_options = ChromeOptions()
    chrome_options.binary_location = profile["binary_location"]
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f'--user-data-dir={profile["chrome_user_data_dir"]}')
    chrome_options.add_argument(f'--profile-directory={profile["profile_directory"]}')
    service = ChromeService(executable_path=profile["executable_path"])
    browser = webdriver.Chrome(service=service, options=chrome_options)
    browser.get('https://www.facebook.com')
    print(
        f'{bcolors.OKGREEN}' "Browser started successfully and navigated to Facebook" + bcolors.ENDC
    )
    logging.info("Browser started successfully and navigated to Facebook")
    return browser

def human_type(element: WebElement, text: str, min_delay: float = 0.05, max_delay: float = 0.2):
    """Types text into a web element one character at a time with a random delay to simulate human typing.

    Args:
        element (WebElement): The Selenium WebElement to type into.
        text (str): The text to type into the element.
        min_delay (float): Minimum delay between key presses.
        max_delay (float): Maximum delay between key presses.
    """
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))

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

def like_posts(browser, num_likes=1):
    """ACTION : Likes posts on a page, randomly skipping between 2 to 6 posts between likes, with detailed logging."""
    print(bcolors.OKBLUE + "ACTION : Likes posts on a page, randomly skipping between 3 to 6 posts between likes, with detailed logging." + bcolors.ENDC)
    start_time = time.time()
    posts_liked = 0
    total_duration = 300  # Total time allocated to perform likes is 5 minutes.
    logging.info("ACTION STARTED: Starting the like posts operation")

    try:
        while posts_liked < num_likes and (time.time() - start_time) < total_duration:
            logging.info("Scrolling to load more posts.")
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.randint(5, 10))  # Random delay to mimic human scrolling and wait for load.

            # Attempt to locate like buttons on the page
            like_buttons = WebDriverWait(browser, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, '//div[@aria-label="Like"]'))
            )

            i = 0
            while i < len(like_buttons):
                like_button = like_buttons[i]
                if like_button.is_displayed() and like_button.is_enabled():
                    try:
                        time.sleep(random.randint(10, 20))  # Random delay before liking

                        # Move to and click the like button
                        ActionChains(browser).move_to_element(like_button).click().perform()
                        posts_liked += 1
                        logging.info(f"Successfully liked post {posts_liked}.")
                        if posts_liked >= num_likes:
                            logging.info("Reached the desired number of likes for this session.")
                            break

                        # Sleep between likes to mimic human behavior and to respect time limits
                        time.sleep(random.randint(2, 5))
                    except Exception as e:
                        logging.warning(f"Failed to like a post at index {i}: {str(e)}")
                        continue

                # Randomize skip posts between 3 and 6
                skip_count = random.randint(3, 6)
                i += skip_count
                logging.info(f"Skipping {skip_count} posts after liking one.")

    except Exception as e:
        logging.error(f"Failed to like posts during session: {str(e)}")
    finally:
        logging.info("ACTION COMPLETED: Like posts operation completed.")

def publish_post(browser):
    """Publishes a post on Facebook."""
    try:
        # Click the "What's on your mind?" area to bring up the post dialog
        whats_on_your_mind = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[3]/div/div[2]/div/div/div/div[1]/div/div[1]/span'))
        )
        whats_on_your_mind.click()
        time.sleep(2)
        
        # Enter the message in the create post text area
        create_post_text = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div[1]/div/div[4]/div/div/div[1]/div/div[2]/div/div/div/form/div/div[1]/div/div/div/div[2]/div[1]/div[1]/div[1]/div/div/div[1]'))
        )
        actions = ActionChains(browser)
        actions.move_to_element(create_post_text).click().send_keys(POST1).perform()
        time.sleep(5)
        
         # Click on the button to add an image
        # add_image_button = WebDriverWait(browser, 10).until(
        #     EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div[1]/div/div[4]/div/div/div[1]/div/div[2]/div/div/div/form/div/div[1]/div/div/div/div[3]/div[1]/div[2]/div/div[1]/div/span/div/div/div[1]/div/div/div[1]'))
        # )
        # add_image_button.click()
        # time.sleep(2)  # Wait for the file input to become accessible

        # # File input for images
        # file_input = WebDriverWait(browser, 10).until(
        #     EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div[1]/div/div[4]/div/div/div[1]/div/div[2]/div/div/div/form/div/div[1]/div/div/div/div[2]/div[1]/div[2]/div/div[1]/div/div/div/div[1]/div/div/div'))
        # )
        # file_input.send_keys(os.getenv('IMAGE1'))  # Use the path from environment variables
        # actions.move_to_element(create_post_text).click().send_keys(POST1).perform()
        
        # Click the publish button
        publish_btn_post = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div[1]/div/div[4]/div/div/div[1]/div/div[2]/div/div/div/form/div/div[1]/div/div/div/div[3]/div[2]/div/div/div[1]'))
        )
        publish_btn_post.click()

        logging.info("Post published successfully.")
    except Exception as e:
        logging.error(f"Failed to publish post: {e}")

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

def scroll_page(browser, scroll_pause_time=1.0, max_scroll_iterations=15):
    """Scroll down a webpage in a way that mimics human scrolling behavior, but slower and more varied."""
    # Start from a smaller scroll and increase incrementally
    step_size = browser.execute_script("return window.innerHeight;") // 4

    for _ in range(max_scroll_iterations):
        # Randomize the scroll distance each time to mimic human inconsistency
        scroll_distance = step_size + random.randint(-step_size // 2, step_size // 2)

        # Scroll down by the calculated distance
        browser.execute_script(f"window.scrollBy(0, {scroll_distance});")

        # Random pause after scrolling to mimic looking at content
        time.sleep(random.uniform(scroll_pause_time, scroll_pause_time * 2))

        # Occasionally mimic a user scrolling up slightly
        if random.random() < 0.1:  # 10% chance to scroll up slightly
            scroll_up_distance = random.randint(step_size // 2, step_size)
            browser.execute_script(f"window.scrollBy(0, -{scroll_up_distance});")
            time.sleep(random.uniform(0.5, 1.0))

        # Dynamically adjust the step size based on the remaining unseen content
        new_height = browser.execute_script("return document.body.scrollHeight")
        scrolled_height = browser.execute_script("return window.pageYOffset;")
        remaining_height = new_height - scrolled_height - step_size * 3

        if remaining_height < browser.execute_script("return window.innerHeight;"):
            break  # Stop if there's not enough unseen content to scroll through

        # Increase the step size to cover more area as we go deeper
        step_size = min(step_size + 50, new_height // 3)

    # Final gentle scroll to adjust the final view, mimicking final user adjustments
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
        # Select a random comment once and store it
        chosen_comment = random.choice(comments)
        
        # Wait for the comment button to be clickable
        comment_button = WebDriverWait(browser, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@aria-label="Leave a comment"]'))
        )
        time.sleep(2)  # Give some time for any overlays to disappear

        # Try clicking using JavaScript if normal click fails
        try:
            comment_button.click()
        except Exception as e:
            browser.execute_script("arguments[0].click();", comment_button)

        time.sleep(5)
        
        input_cmnt = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@aria-label="Write a comment…"]'))
        )
        input_cmnt.click()
        time.sleep(5)  # Short pause to ensure the input is ready
        human_type(input_cmnt, chosen_comment)  # Use the randomly selected comment
        time.sleep(5)
        input_cmnt.send_keys(Keys.ENTER)
        time.sleep(5)
        logging.info(f"Commented on post successfully, comment: {chosen_comment}")
        
        # Check if the close comment button is displayed and clickable
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
    """Shares posts on a page, skipping a set number of posts between shares."""
    logging.info("ACTION STARTED: Sharing posts")
    start_time = time.time()
    posts_shared = 0
    shared_indices = set()  # Set to keep track of indices of shared posts

    while posts_shared < num_shares and (time.time() - start_time) < 300:
        scroll_down(browser)
        time.sleep(10)  # Ensure the page loads completely

        share_buttons = WebDriverWait(browser, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[@aria-label="Send this to friends or post it on your profile."]'))
        )

        for i in range(len(share_buttons)):
            if i % (skip_posts + 1) == 0 and i not in shared_indices:  # Check if the post is to be shared and not already shared
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
                        shared_indices.add(i)  # Mark this index as shared
                        logging.info(f"Successfully shared post {posts_shared}")
                        if posts_shared >= num_shares:
                            logging.info("ACTION COMPLETED: All requested posts have been shared successfully.")
                            return
                        time.sleep(60)  # Delay between shares

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
        print(bcolors.OKBLUE + "ACTION : Inviting friends." + bcolors.ENDC)
        browser.get('https://web.facebook.com/friends/suggestions')
        time.sleep(5)  # Allow the page to load content

        # Fetch the 'Add Friend' buttons
        buttons = WebDriverWait(browser, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[starts-with(@aria-label, 'Add Friend')]"))
        )

        invitations_sent = 0
        i = 0  # Start with the first element
        while invitations_sent < num_invitations and i < len(buttons):
            try:
                button = buttons[i]
                if button.is_displayed():
                    button.click()
                    time.sleep(5)  # Wait some time between clicks to mimic human behavior
                    logging.info(f"Invited friend {invitations_sent + 1} successfully")
                    invitations_sent += 1

                # Increment i to skip two people after inviting one
                i += 3  # Skip two people after sending one invite (1 invited + 2 skipped)

            except StaleElementReferenceException:
                logging.warning("Stale Element Reference detected, refetching elements.")
                # Refetch the elements if a stale element reference occurs
                buttons = WebDriverWait(browser, 20).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[starts-with(@aria-label, 'Add Friend')]"))
                )
                continue  # Continue from the same index, potentially adjusted if elements are fewer
            except Exception as e:
                logging.error(f"Error when trying to invite: {e}")
                i += 1  # Attempt the next person in case of other errors

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

def infinite_scroll_with_refresh(browser, timeout=300):
    """Infinite scroll with refresh if no new data is loaded after scrolling."""
    logging.info("ACTION STARTED: Starting Infinite scroll with refresh")
    print(bcolors.OKBLUE + "ACTION : Starting Infinite scroll with refresh." + bcolors.ENDC)
    old_height = browser.execute_script("return document.body.scrollHeight")
    start_time = time.time()

    while time.time() - start_time < timeout:
        # Scroll down
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        logging.info("Scrolled to bottom of the page.")
        
        # Wait for the page to load
        time.sleep(10)
        
        # Calculate the new scroll height and compare it with the last scroll height
        new_height = browser.execute_script("return document.body.scrollHeight")
        if new_height == old_height:
            # If heights are the same after waiting, refresh the page and continue
            logging.info("No new data loaded; refreshing page...")
            browser.refresh()
            time.sleep(10)  # Wait for the page to load after refresh
        else:
            # Update the old height to the new height for the next comparison
            old_height = new_height
            logging.info("New data loaded, updated scroll height.")

        # Simulate human-like scrolling with a slight random delay
        time.sleep(random.uniform(2, 5))

    logging.info("ACTION COMPLETED: Finished scrolling or timeout reached.")

def telegram_bot_sendtext(bot_message):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Format: YYYY-MM-DD HH:MM:SS
    full_message = f"{current_time} - {bot_message}"

    send_text = 'https://api.telegram.org/bot' + BOT_TOKEN + '/sendMessage?chat_id=' + CHAT_ID + '&parse_mode=Markdown&text=' + full_message

    response = requests.get(send_text)

    return response.json()

def telegram_bot_send_document(file_path):
    bot_token = '6942917087:AAHM1cr4rZjDMoTBjrzFzZcup9_IkdwjVoM'
    bot_chatID = '1318052693'
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendDocument'
    
    with open(file_path, 'rb') as document:
        files = {
            'document': document
        }
        data = {
            'chat_id': CHAT_ID
        }
        response = requests.post(url, files=files, data=data)
    
    return response.json()



def main(profile):
    """Main function to manage browser session and distribute actions continuously over 24 hours."""
    logging.basicConfig(filename=f'fbwarming_{profile["user"]}.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    browser = setup_browser()  # Set up browser once outside the loop
    actions = [
         like_posts,   share_post, invite_friends, 
         like_posts,   share_post, invite_friends, 
         like_posts, invite_friends,
         invite_friends,
         invite_friends,
         invite_friends,
         invite_friends,
         invite_friends,
         invite_friends,
         invite_friends,
        ]
    num_actions = len(actions)
    interval = 300 / num_actions  # Distribute actions evenly across 24 hours

    cycle_count = 0  # Initialize cycle count
    while True:  # Infinite loop to keep running the actions
        logging.info(f"Starting action cycle {cycle_count + 1}")
        telegram_bot_sendtext("Start warming")
        start_cycle = time.time()
        for action in actions:
            action_name = action.__name__
            try:
                action_start = time.time()
                action(browser)  # Execute the action
                action_duration = time.time() - action_start
                sleep_time = max(0, interval - action_duration)  # Calculate remaining time to sleep
                time.sleep(sleep_time) 
            except Exception as e:
                logging.error(f"An error occurred during {action_name}: {e}")
                # Optionally implement recovery or additional logging here

        # After completing all actions, check total elapsed time and adjust if necessary
        cycle_duration = time.time() - start_cycle
        if cycle_duration < 250:
            time.sleep(250 - cycle_duration)  # Ensure the cycle takes exactly 24 hours

        cycle_count += 1  # Increment cycle count after each complete run
        logging.info(f"Completed action cycle {cycle_count}. Waiting to start next cycle.")
        telegram_bot_send_document(f'fbwarming_{profile["user"]}.log')
        telegram_bot_sendtext("Finish warming")

if __name__ == "__main__":
    profiles = load_profiles()
    for profile in profiles:
        # Consider threading or multiprocessing based on your concurrency needs
        main(profile)