import json
import os
import glob
import time
import random
import shutil
import pathlib
from contextlib import contextmanager

from better_proxy import Proxy

from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager

from bot.config import settings
from bot.utils import logger


def get_session_names() -> list[str]:
    session_names = [os.path.splitext(os.path.basename(file))[0] for file in glob.glob("sessions/*.session")]

    return session_names


def get_proxies() -> list[Proxy]:
    if settings.USE_PROXY_FROM_FILE:
        with open(file="bot/config/proxies.txt", encoding="utf-8-sig") as file:
            proxies = [Proxy.from_str(proxy=row.strip()).as_url for row in file]
    else:
        proxies = []

    return proxies


def escape_html(text: str) -> str:
    text = str(text)
    return text.replace('<', '\\<').replace('>', '\\>')


web_options = ChromeOptions
web_service = ChromeService
web_manager = ChromeDriverManager
web_driver = webdriver.Chrome

if not pathlib.Path("webdriver").exists() or len(list(pathlib.Path("webdriver").iterdir())) == 0:
    logger.info("Downloading webdriver. It may take some time...")
    pathlib.Path("webdriver").mkdir(parents=True, exist_ok=True)
    webdriver_path = pathlib.Path(web_manager().install())
    shutil.move(webdriver_path, f"webdriver/{webdriver_path.name}")
    logger.info("Webdriver downloaded successfully")

webdriver_path = next(pathlib.Path("webdriver").iterdir()).as_posix()

device_metrics = {"width": 375, "height": 812, "pixelRatio": 3.0}
user_agent = "Mozilla/5.0 (Linux; Android 13; RMX3630 Build/TP1A.220905.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/125.0.6422.165 Mobile Safari/537.36"

mobile_emulation = {
    "deviceMetrics": device_metrics,
    "userAgent": user_agent,
}

options = web_options()

options.add_experimental_option("mobileEmulation", mobile_emulation)

options.add_argument("--headless")
options.add_argument("--log-level=3")
if os.name == 'posix':
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')


@contextmanager
def create_webdriver():
    driver = web_driver(service=web_service(webdriver_path), options=options)
    try:
        yield driver
    finally:
        driver.quit()

# Other way
def login_in_browser(auth_url: str, proxy: str):
    with create_webdriver() as driver:
        if proxy:
            proxy_options = {
                'proxy': {
                    'http': proxy,
                    'https': proxy,
                }
            }
        else:
            proxy_options = None
        driver = web_driver(service=web_service(webdriver_path), options=options, seleniumwire_options=proxy_options)

        driver.get(auth_url)
        time.sleep(3)

        response_text = '{}'

        for request in driver.requests:
            if request.url == "https://api.sograph.xyz/api/login/web2":
                response_text = request.response.body.decode('utf-8')
                response_json = json.loads(response_text)
                signature = response_json.get('data', {}).get('signature', {})

    return signature