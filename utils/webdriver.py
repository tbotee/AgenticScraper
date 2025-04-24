from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def setup_webdriver(headless=True):
    """
    Set up and return a configured WebDriver instance.
    
    Args:
        headless (bool): Whether to run the browser in headless mode
        
    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance
    """
    options = Options()
    if headless:
        options.add_argument("--headless")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # Add user agent to avoid detection
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36")
    
    # Create the driver with configured options
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    # Set page load timeout
    driver.set_page_load_timeout(30)
    
    return driver