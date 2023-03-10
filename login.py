import logging
import time

from selenium import webdriver

# 获取缺口位置
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from fetch import UA
from util import wechat_push_img, wechat_push, get_latest_sms_code


def cookie_to_str(cookies_dict):
    login_cookie = ''
    for item in cookies_dict:
        login_cookie += item["name"] + '=' + item['value'] + '; '
    print("Cookie Got: " + login_cookie)
    return login_cookie


def get_chrome_options():
    chrome_options = Options()
    options = ['--disable-gpu', '--disable-impl-side-painting', '--disable-gpu-sandbox',
               '--disable-accelerated-2d-canvas', '--disable-accelerated-jpeg-decoding', '--no-sandbox',
               '--test-type=ui', '--headless', '--disable-dev-shm-usage', '--dns-prefetch-disable',
               '--disable-browser-side-navigation',
               ]

    for opt in options:
        chrome_options.add_argument(opt)

    # 默认 UA 容易不能通过验证码, 所以加个自定义UA.
    chrome_options.add_argument("user-agent=" + UA)

    return chrome_options


def password_login(username, password):
    print("尝试账号密码登录...")
    with webdriver.Chrome(options=get_chrome_options()) as driver:
        # 登录
        login_timeout = 60

        driver.set_page_load_timeout(login_timeout)
        driver.set_script_timeout(login_timeout)

        driver.get('https://i.qq.com/')
        driver.implicitly_wait(login_timeout)

        try:
            driver.switch_to.frame('login_frame')
        except Exception as e:
            wechat_push("切换到 login_frame 失败: " + str(e))
            wechat_push_img(driver.get_screenshot_as_base64())

        driver.find_element(By.ID, 'switcher_plogin').click()
        driver.find_element(By.ID, 'u').clear()
        driver.find_element(By.ID, 'u').send_keys(username)
        driver.find_element(By.ID, 'p').clear()
        driver.find_element(By.ID, 'p').send_keys(password)
        time.sleep(1)
        driver.find_element(By.ID, 'login_button').click()
        time.sleep(5)

        for i2 in range(0, 10):
            time.sleep(1)
            if "user.qzone.qq.com" in driver.current_url:
                break
        else:
            wechat_push("登录失败! 凭据错误/触发风控, 尝试验证手机短信")
            wechat_push_img(driver.get_screenshot_as_base64())

        try:
            wechat_push("尝试发送手机验证码登录...")
            driver.switch_to.frame('verify')
            driver.find_element(By.CLASS_NAME, 'input-area__sms-btn').click()
            time.sleep(1)
            driver.find_element(By.XPATH, '//input[@maxlength="6"]').send_keys(get_latest_sms_code())
            time.sleep(1)
            driver.find_element(By.CLASS_NAME, 'qui-button__inner').click()
        except Exception as e:
            wechat_push("尝试手机验证码登录失败: " + str(e))
            wechat_push_img(driver.get_screenshot_as_base64())

        for i2 in range(0, 10):
            time.sleep(1)
            if "user.qzone.qq.com" in driver.current_url:
                break
        else:
            wechat_push_img(driver.get_screenshot_as_base64())
            raise Exception("登录失败!")

        return cookie_to_str(driver.get_cookies())


def qr_login():
    with webdriver.Chrome(options=get_chrome_options()) as driver:
        # 登录
        login_timeout = 60

        driver.set_page_load_timeout(login_timeout)
        driver.set_script_timeout(login_timeout)
        driver.get('https://i.qq.com/')
        driver.implicitly_wait(login_timeout)

        driver.switch_to.frame('login_frame')
        time.sleep(3)
        b64 = driver.find_element(By.ID, "qrlogin_img").screenshot_as_base64
        print("二维码: " + b64)
        wechat_push_img(b64)

        for i2 in range(0, 120):
            time.sleep(1)
            if "user.qzone.qq.com" in driver.current_url:
                break
        else:
            wechat_push_img(driver.get_screenshot_as_base64())
            raise Exception("登录失败! 二维码登录超时!")

        global last_cookie
        last_cookie = driver.get_cookies()

        return cookie_to_str(driver.get_cookies())
