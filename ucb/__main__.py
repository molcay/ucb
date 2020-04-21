import os
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

ROOT_DIR = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
COURSE_LIST_FILE = os.path.join(ROOT_DIR, 'course_list.txt')

SLEEP_AFTER_BUY = 10
IMPLICIT_WAIT = 10
SLEEP_IF_REGISTER_EXIST = 3


def _get_course_list():
    with open(COURSE_LIST_FILE) as f:
        lines = f.readlines()
        return [line.replace('\n', '') for line in lines]


def _login(driver, user_email=None, user_password=None):
    driver.get('https://www.udemy.com/')
    try:
        login_btn = driver.find_element_by_css_selector('div.header--gap-xs--1q0SU:nth-child(8) > a:nth-child(1) > span:nth-child(1)')
        login_btn.click()
        print('[NEW UI]: login')
    except NoSuchElementException:
        login_btn = driver.find_element_by_css_selector('div.dropdown:nth-child(6) > div:nth-child(1) > button:nth-child(1)')
        login_btn.click()
        print('[OLD UI]: login')
    finally:
        email_input = driver.find_element_by_css_selector('#email--1')
        email_input.send_keys(user_email)

        pwd_input = driver.find_element_by_css_selector('#id_password')
        pwd_input.send_keys(user_password)

        submit_btn = driver.find_element_by_css_selector('#submit-id-submit')
        submit_btn.click()


def _buy(driver, url):
    driver.get(url)
    search_text_for_buy = 'Hemen kaydolun'
    try:
        buy_btn = driver.find_element_by_css_selector('.buy-button > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > button:nth-child(1)')
        button_text = buy_btn.find_element_by_css_selector('span').text.strip()
        if button_text == search_text_for_buy:
            print(f'[{url}] sayfasında [{search_text_for_buy}] bulundu. {SLEEP_IF_REGISTER_EXIST} saniye kadar uyunuyor')
            time.sleep(SLEEP_IF_REGISTER_EXIST)
            buy_btn.click()
        else:
            print(f'[{url}] sayfasında [{search_text_for_buy}] bulunamadı!')
            if button_text == 'Kursa git':
                print(f'[{url}] kursu zaten alınmış!')
        print('[NEW UI]: buy')
    except NoSuchElementException:
        print('[OLD UI]: buy')
        buy_btn = driver.find_element_by_css_selector('.course-cta')
        button_text = buy_btn.text.strip()
        if button_text == search_text_for_buy:
            print(
                f'[{url}] sayfasında [{search_text_for_buy}] bulundu. {SLEEP_IF_REGISTER_EXIST} saniye kadar uyunuyor')
            time.sleep(SLEEP_IF_REGISTER_EXIST)
            buy_btn.click()
        else:
            print(f'[{url}] sayfasında [{search_text_for_buy}] bulunamadı!')
            if button_text == 'Kursa git':
                print(f'[{url}] kursu zaten alınmış!')


def get_credentials_from_env():
    return os.environ['UCB_UDEMY_EMAIL'], os.environ['UCB_UDEMY_PASSWORD']


def main():
    email, password = get_credentials_from_env()
    course_list = _get_course_list()

    driver = webdriver.Firefox()
    driver.implicitly_wait(IMPLICIT_WAIT)
    try:
        _login(driver, user_email=email, user_password=password)

        time.sleep(7)

        for i, course_url in enumerate(course_list, 1):
            try:
                print(f'Navigating to #{i} of {len(course_list)}: {course_url}')
                print(f'{len(course_list)} içinden {i}. için [{course_url}] sayfasına gidiliyor...')
                _buy(driver, course_url)
                print(f'{len(course_list)} içinden {i}. için [{course_url}] sayfasında satın alma sonrası {SLEEP_AFTER_BUY} saniye kadar bekleniyor...')
            except Exception as e:
                print(f'Satın alma başarısız. {SLEEP_AFTER_BUY} saniye kadar bekleniyor.')
                print(e)
            finally:
                time.sleep(SLEEP_AFTER_BUY)
    finally:
        time.sleep(15)
        driver.close()


if __name__ == '__main__':
    main()
    # TODO: @molcay add Logger config
