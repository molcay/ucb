import json
import os
import time
from logging.handlers import TimedRotatingFileHandler, logging

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

ROOT_DIR = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
COURSE_FILENAME = 'courses.json'
COURSE_LIST_FILE = os.path.join(ROOT_DIR, COURSE_FILENAME)

SLEEP_AFTER_BUY = 20
IMPLICIT_WAIT = 15
SLEEP_BEFORE_CLICK = 10

TEXT_FOR_UI = {
    'register': 'Hemen kaydolun',
    'goto': 'Kursa git',
    'buy': 'Hemen satın al',
}


class Logger:
    def __init__(self, path, logger_name):
        self.path = path
        self.logger_name = logger_name

    def logger_init(self):
        log_path = self.path
        logger_ = logging.getLogger(self.logger_name)
        logger_.setLevel(logging.DEBUG)

        # log formatting
        log_format = '%(asctime)s [%(levelname)s] (%(name)s) - [%(filename)s:%(lineno)d]: ' \
                     '[%(threadName)s] - %(message)s '
        formatter = logging.Formatter(log_format)

        # log config
        handler = TimedRotatingFileHandler(log_path, when="midnight", interval=1, encoding="utf-8")
        handler.setFormatter(formatter)
        logger_.addHandler(handler)

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger_.addHandler(handler)

        return logger_


def get_app_logger(is_prod: bool = False):
    logger_ = logging.getLogger('app')

    log_file_dir = 'logs'
    if is_prod:
        log_file_dir = '/var/log/'

    if not logger_.hasHandlers():
        return Logger(os.path.join(ROOT_DIR, f'{log_file_dir}/app.log'), 'app').logger_init()

    return logger_


logger = get_app_logger()


def _get_course_list():
    with open(COURSE_LIST_FILE) as f:
        return json.loads(f.read())


def _login(driver, user_email=None, user_password=None):
    driver.get('https://www.udemy.com/')
    try:
        login_btn = driver.find_element_by_css_selector(
            'div.header--gap-xs--1q0SU:nth-child(8) > a:nth-child(1) > span:nth-child(1)'
        )  # If UI is the new UI
        login_btn.click()
        logger.info('[NEW UI]: login')
    except NoSuchElementException:
        login_btn = driver.find_element_by_css_selector(
            'div.dropdown:nth-child(6) > div:nth-child(1) > button:nth-child(1)'
        )  # If UI is the old UI
        login_btn.click()
        logger.info('[OLD UI]: login')
    finally:
        email_input = driver.find_element_by_css_selector('#email--1')
        email_input.send_keys(user_email)

        pwd_input = driver.find_element_by_css_selector('#id_password')
        pwd_input.send_keys(user_password)

        submit_btn = driver.find_element_by_css_selector('#submit-id-submit')
        submit_btn.click()


def _buy(driver, url):
    search_text_for_buy = TEXT_FOR_UI['register']
    status = 'BEGINNING'

    driver.get(url)

    try:
        button_cta = driver.find_element_by_css_selector(
            '.buy-button > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > button:nth-child(1)'
        )
        button_cta_text = button_cta.find_element_by_css_selector('span').text.strip()
        if button_cta_text == search_text_for_buy:
            logger.info(
                f'[{url}] sayfasında [{search_text_for_buy}] bulundu. {SLEEP_BEFORE_CLICK} saniye kadar uyunuyor'
            )
            time.sleep(SLEEP_BEFORE_CLICK)
            button_cta.click()
            status = 'DONE'
        else:
            logger.info(f'[{url}] sayfasında [{search_text_for_buy}] bulunamadı!')
            if button_cta_text == TEXT_FOR_UI['goto']:
                logger.warning(f'[{url}] kursu zaten alınmış!')
                status = 'ALREADY_BOUGHT'
            else:
                status = 'UNKNOWN'
                logger.warning(f'[{url}] kursunda CTA buttonunda [{button_cta_text}] yazıyordu...')
        logger.debug('[NEW UI]: buy')
    except NoSuchElementException:
        logger.debug('[OLD UI]: buy')
        button_cta = driver.find_element_by_css_selector('.course-cta')
        button_cta_text = button_cta.text.strip()
        if button_cta_text == search_text_for_buy:
            logger.info(
                f'[{url}] sayfasında [{search_text_for_buy}] bulundu. {SLEEP_BEFORE_CLICK} saniye kadar uyunuyor'
            )
            time.sleep(SLEEP_BEFORE_CLICK)
            button_cta.click()
            status = 'DONE'
        else:
            logger.warning(f'[{url}] sayfasında [{search_text_for_buy}] bulunamadı!')
            if button_cta_text == TEXT_FOR_UI['goto']:
                logger.warning(f'[{url}] kursu zaten alınmış!')
                status = 'ALREADY_BOUGHT'
            else:
                status = 'UNKNOWN'
                logger.warning(f'[{url}] kursunda CTA buttonunda [{button_cta_text}] yazıyordu...')
    finally:
        return status


def get_credentials_from_env():
    return os.environ['UCB_UDEMY_EMAIL'], os.environ['UCB_UDEMY_PASSWORD']


def write_json_to_file(data, filename=COURSE_LIST_FILE):
    logger.info('Saving data to the file')
    with open(filename, 'w') as f:
        f.write(json.dumps(data))
    logger.info(f'Saved data to the file: [{filename}]')


def get_options():
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:75.0) Gecko/20100101 Firefox/75.0'

    options = webdriver.FirefoxOptions()
    # options.add_argument('headless')
    # specify the desired user agent
    options.add_argument(f'user-agent={user_agent}')

    return options


def main():
    email, password = get_credentials_from_env()
    courses = _get_course_list()

    driver = webdriver.Firefox(options=get_options())
    driver.implicitly_wait(IMPLICIT_WAIT)
    try:
        _login(driver, user_email=email, user_password=password)

        time.sleep(7)

        for i, course in enumerate(courses[:], 1):
            if course['status'] in ['DONE', 'ALREADY_BOUGHT']:
                logger.info(f'Kurs #{i} geçiliyor. Satın alma durumu: {course["status"]}')
                continue
            course_url = course['url']
            try:
                logger.info(f'Navigating to #{i} of {len(courses)}: {course_url}')
                logger.info(f'{len(courses)} içinden {i}. için [{course_url}] sayfasına gidiliyor...')
                status = _buy(driver, course_url)
                logger.info(
                    f'{len(courses)} içinden {i}. için [{course_url}] sayfasında satın alma sonrası {SLEEP_AFTER_BUY} saniye kadar bekleniyor...'
                )
                course['status'] = status
            except Exception as e:
                course['status'] = 'FAILED'
                logger.error(f'Satın alma başarısız. {SLEEP_AFTER_BUY} saniye kadar bekleniyor.')
                logger.error(e)
            finally:
                write_json_to_file(courses)
                time.sleep(SLEEP_AFTER_BUY)
    finally:
        time.sleep(15)
        driver.close()


if __name__ == '__main__':
    main()
