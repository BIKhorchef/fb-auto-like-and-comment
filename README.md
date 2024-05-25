# Facebook Auto Like, Comment, and More

This Python script automates interactions on Facebook, including liking posts, commenting, inviting friends, and more. It uses Selenium with WebDriver for browser automation.

## Features

- **Proxy Support**: Supports proxy configuration to perform actions from different locations.
- **Logging**: Detailed logging of actions performed and errors encountered.
- **Telegram Integration**: Sends notifications via Telegram when actions start and finish.
- **Customizable Profiles**: Configurable profiles for different Facebook accounts.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/BIKhorchef/facebook-auto-like-comment.git
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Set up environment variables:
   - `USER`: Your Facebook username
   - `PASSWORD`: Your Facebook password
   - `TFA_SECRET`: Your Two-factor Authentication (TFA) secret key
   - `BOT_TOKEN`: Your Telegram bot token
   - `CHAT_ID`: Your Telegram chat ID
   - `GROUP_LINKS`: Comma-separated list of Facebook group links
   - `MESSAGES`: Comma-separated list of messages for comments

4. Configuration:
   - Profiles: Edit profiles.json to configure different profiles with proxy settings and expected locations.
```bash
{
    "profiles": [
        {
            "user": "user1",
            "chrome_user_data_dir": "C:\\Users\\AppData\\Local\\Google\\Chrome for Testing\\User Data",
            "profile_directory": "Default",
            "executable_path": "C:\\Chrome\\chromedriver-win64\\chromedriver.exe",
	        "binary_location": "C:\\Chrome\\chrome-win64\\chrome.exe",
            "proxy_host": "rproxy",
            "proxy_port": "0000",
            "proxy_user": "proxy",
            "proxy_pass": "proxy;",
            "expected_country": "BE",
            "expected_city": "brussels"
        }
    ]
}
```

## Usage

Run the script with:

```bash
python fbwarming.py
