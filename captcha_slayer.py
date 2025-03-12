import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import cv2
import numpy as np
from PIL import Image
import pytesseract
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Banner
BANNER = f"""
{Fore.GREEN}============================================================{Style.RESET_ALL}
{Fore.RED}      CAPTCHA Slayer v1.0 - Auto CAPTCHA Solver      {Style.RESET_ALL}
{Fore.GREEN}============================================================{Style.RESET_ALL}
{Fore.CYAN} Coded by: Shiboshree Roy | Date: {time.strftime('%Y-%m-%d')} {Style.RESET_ALL}
{Fore.YELLOW} Target: User-Defined Website | Mode: Autonomous {Style.RESET_ALL}
{Fore.GREEN}============================================================{Style.RESET_ALL}
"""

# Function to initialize Selenium WebDriver
def init_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run headless
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(service=Service(), options=chrome_options)
        logging.info(f"{Fore.GREEN}WebDriver initialized.{Style.RESET_ALL}")
        return driver
    except Exception as e:
        logging.error(f"{Fore.RED}WebDriver failed: {e}{Style.RESET_ALL}")
        raise

# Function to preprocess CAPTCHA image
def preprocess_image(image_path: str) -> np.ndarray:
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    kernel = np.ones((3, 3), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    dilated = cv2.dilate(cleaned, kernel, iterations=1)
    return dilated

# Function to solve text-based CAPTCHA
def solve_captcha(image_path: str) -> str:
    processed_img = preprocess_image(image_path)
    temp_path = "processed_captcha.png"
    cv2.imwrite(temp_path, processed_img)
    custom_config = r'--oem 3 --psm 6'
    captcha_text = pytesseract.image_to_string(Image.open(temp_path), config=custom_config).strip()
    os.remove(temp_path)
    logging.info(f"{Fore.YELLOW}Extracted CAPTCHA text: {captcha_text}{Style.RESET_ALL}")
    return captcha_text

# Function to detect and solve CAPTCHA on a webpage
def handle_captcha(driver: webdriver.Chrome, captcha_img_xpath: str, input_xpath: str, submit_xpath: str) -> bool:
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, captcha_img_xpath))
        )
        logging.info(f"{Fore.GREEN}CAPTCHA detected.{Style.RESET_ALL}")
        
        driver.save_screenshot("screenshot.png")
        captcha_element = driver.find_element(By.XPATH, captcha_img_xpath)
        location = captcha_element.location
        size = captcha_element.size
        
        img = Image.open("screenshot.png")
        left = location['x']
        top = location['y']
        right = left + size['width']
        bottom = top + size['height']
        captcha_img = img.crop((left, top, right, bottom))
        captcha_img.save("captcha.png")
        
        captcha_text = solve_captcha("captcha.png")
        
        if not captcha_text:
            logging.error(f"{Fore.RED}Failed to extract CAPTCHA text.{Style.RESET_ALL}")
            return False
        
        input_field = driver.find_element(By.XPATH, input_xpath)
        input_field.clear()
        input_field.send_keys(captcha_text)
        
        submit_button = driver.find_element(By.XPATH, submit_xpath)
        submit_button.click()
        
        time.sleep(2)
        if "CAPTCHA" not in driver.page_source:
            logging.info(f"{Fore.GREEN}CAPTCHA solved successfully.{Style.RESET_ALL}")
            return True
        else:
            logging.warning(f"{Fore.YELLOW}CAPTCHA solution failed, retrying may be needed.{Style.RESET_ALL}")
            return False
            
    except TimeoutException:
        logging.error(f"{Fore.RED}CAPTCHA not found on page.{Style.RESET_ALL}")
        return False
    except Exception as e:
        logging.error(f"{Fore.RED}Error solving CAPTCHA: {e}{Style.RESET_ALL}")
        return False
    finally:
        for file in ["screenshot.png", "captcha.png"]:
            if os.path.exists(file):
                os.remove(file)

# Function to get website URL from user
def get_website_url_from_user() -> str:
    print(f"{Fore.YELLOW}Enter the website URL containing the CAPTCHA (e.g., https://example.com/captcha-page):{Style.RESET_ALL}")
    while True:
        url = input(f"{Fore.CYAN}>> {Style.RESET_ALL}").strip()
        if url.startswith("http://") or url.startswith("https://"):
            print(f"{Fore.GREEN}Target acquired: {url}{Style.RESET_ALL}")
            return url
        else:
            print(f"{Fore.RED}Invalid URL. Must start with 'http://' or 'https://'. Try again.{Style.RESET_ALL}")

# Main function
def main(captcha_img_xpath: str, input_xpath: str, submit_xpath: str):
    print(BANNER)
    target_url = get_website_url_from_user()
    driver = init_driver()
    
    try:
        logging.info(f"{Fore.CYAN}Navigating to target: {target_url}{Style.RESET_ALL}")
        driver.get(target_url)
        
        max_attempts = 3
        for attempt in range(max_attempts):
            if handle_captcha(driver, captcha_img_xpath, input_xpath, submit_xpath):
                logging.info(f"{Fore.GREEN}Mission accomplished.{Style.RESET_ALL}")
                break
            else:
                logging.warning(f"{Fore.YELLOW}Attempt {attempt + 1}/{max_attempts} failed.{Style.RESET_ALL}")
                time.sleep(2)
        else:
            logging.error(f"{Fore.RED}All attempts failed. CAPTCHA too strong.{Style.RESET_ALL}")
            
    finally:
        driver.quit()
        logging.info(f"{Fore.CYAN}WebDriver terminated.{Style.RESET_ALL}")

# Example usage (customize XPaths for your target website)
if __name__ == "__main__":
    # Default XPaths (update these based on the target website)
    CAPTCHA_IMG_XPATH = "//img[@class='captcha-image']"  # XPath to CAPTCHA image
    INPUT_XPATH = "//input[@id='captcha-input']"        # XPath to text input field
    SUBMIT_XPATH = "//button[@type='submit']"           # XPath to submit button
    
    main(CAPTCHA_IMG_XPATH, INPUT_XPATH, SUBMIT_XPATH)