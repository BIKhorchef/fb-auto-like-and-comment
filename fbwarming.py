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


# Initialize logging
logging.basicConfig(filename='fbwarming.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
TFA_SECRET = os.getenv('TFA_SECRET')

# Create TOTP object for 2FA
totp = pyotp.TOTP(TFA_SECRET)

def setup_browser():
    """Initializes and returns a Chrome WebDriver using a specific Chrome profile and custom driver path."""
    chrome_driver_path = r'C:\Chrome\chromedriver-win64\chromedriver.exe'
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    user_data_dir = r'C:\Users\badrk\AppData\Local\Google\Chrome for Testing\User Data'
    chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
    chrome_options.add_argument('--profile-directory=Profile 1')
    service = ChromeService(executable_path=chrome_driver_path)
    browser = webdriver.Chrome(service=service, options=chrome_options)
    browser.get('https://www.facebook.com')
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


def like_posts(browser, num_likes=5, skip_posts=4):
    """Likes posts on a page, skipping a set number of posts between likes."""
    start_time = time.time()
    posts_liked = 0
    total_duration = 300  # Total time allocated to perform likes is 5 minutes.

    try:
        while posts_liked < num_likes and (time.time() - start_time) < total_duration:
            # Scroll down to load more posts
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.randint(5, 10))  # Random delay to mimic human scrolling and wait for load.

            # Attempt to locate like buttons on the page
            like_buttons = WebDriverWait(browser, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, '//div[@aria-label="Like" or @aria-label="React"]'))
            )

            # Process the buttons while considering the skip logic
            for i in range(0, len(like_buttons), skip_posts + 1):  # Skip the specified number of posts after liking one
                like_button = like_buttons[i]
                if like_button.is_displayed() and like_button.is_enabled():
                    try:
                        # Move to and click the like button
                        ActionChains(browser).move_to_element(like_button).click().perform()
                        posts_liked += 1
                        logging.info(f"Successfully liked post {posts_liked}")
                        if posts_liked >= num_likes:
                            break
                        # Sleep between likes to mimic human behavior and to respect time limits
                        time.sleep(random.randint(30, 60))
                    except Exception as e:
                        logging.warning(f"Failed to like a post: {e}")
                        continue

    except Exception as e:
        logging.error(f"Failed to like posts during session: {e}")


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
    groups_links_list = [
        "https://www.facebook.com/groups/1636819003107038"
    ]
    message = "Hiii my friends, how are you doing today?"

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
            ActionChains(browser).move_to_element(input_box).click().send_keys(message).perform()

            # Post the message
            post_button = WebDriverWait(browser, 20).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div[1]/div/div[4]/div/div/div[1]/div/div[2]/div/div/div/div/div[1]/form/div/div[1]/div/div/div[1]/div/div[3]/div[3]/div/div"))
            )
            post_button.click()
            logging.info(f"Successfully posted to {group_link}.")
            time.sleep(10)  # Wait for post to complete
        except Exception as e:
            # browser.save_screenshot('error.png')  # Save a screenshot on error
            logging.error(f"Failed to post to {group_link}: {e}")


def scroll_page(browser):
    """Scroll down and up to simulate more human-like interaction and trigger dynamic content."""
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # Scroll to bottom
    time.sleep(3)  # Wait for the page to load
    browser.execute_script("window.scrollTo(0, 0);")  # Scroll back to top
    time.sleep(2)  # Wait for the page to stabilize


def scroll_down(browser):
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)


def comment_on_posts(browser, comments):
    scroll_page(browser)
    try:
        # Wait for 5 seconds to allow the page to load more content
        time.sleep(5)
        WebDriverWait(browser, 20).until(
            EC.presence_of_element_located((By.XPATH, '//*[@aria-label="Leave a comment"]'))
        ).click()
        time.sleep(5)
        
        input_cmnt = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@aria-label="Write a comment…"]'))
        )
        input_cmnt.click()
        time.sleep(5)  # Short pause to ensure the input is ready
        input_cmnt.send_keys(comments[0])
        time.sleep(5)
        input_cmnt.send_keys(Keys.ENTER)
        close_comment = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@aria-label="Close"]'))
        )
        close_comment = browser.find_element(By.XPATH, '//*[@aria-label="Close"]')
        if close_comment.is_displayed():
            close_comment.click()
        time.sleep(5)
        logging.info("Commented on post successfully, comment: " + comments[0])
        scroll_down(browser)
    except NoSuchElementException:
        logging.error("Comment button or input box not found.")
    except ElementNotInteractableException:
        logging.error("Element not interactable at the time of interaction.")
    except TimeoutException:
        logging.error("Timeout while waiting for the elements.")
        browser.save_screenshot('timeout_error.png')
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")
        browser.save_screenshot('error.png')


def share_post(browser, num_shares=5, skip_posts=4):
    """Shares posts on a page, skipping a set number of posts between shares."""
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
                            return
                        time.sleep(60)  # Delay between shares

                except Exception as e:
                    logging.warning(f"Failed to share a post: {e}")
                    continue

    logging.error("Failed to complete sharing due to some issues.")


def invite_friends(browser, num_invitations=5):
    try:
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
                    logging.info("Invited a friend successfully")
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

    except NoSuchElementException:
        logging.error("Invite button not found.")
    except ElementNotInteractableException:
        logging.error("Element not interactable at the time of interaction.")
    except TimeoutException:
        logging.error("Timeout while waiting for the elements.")
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")


def main():
    """Main function to manage browser session."""
    browser = setup_browser()
    try:
        time.sleep(5)
        # like_posts(browser)
        share_post(browser)
    except Exception as e:
        logging.error(f"An error occurred during the login process: {e}")



if __name__ == "__main__":
    main()
