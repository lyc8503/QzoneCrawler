import logging
import random
import time

import requests
from selenium import webdriver
from selenium.webdriver import ActionChains
import numpy as np
from PIL import Image
import cv2


# 以下为登录部分

# 获取缺口位置
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from fetch import UA
from util import wechat_push_img

last_cookie = []

# 获取图片缺口位置
def get_postion(chunk, canves):
    otemp = chunk
    oblk = canves
    target = cv2.imread(otemp, 0)
    template = cv2.imread(oblk, 0)
    # w, h = target.shape[::-1]
    temp = '/tmp/temp.jpg'
    targ = '/tmp/targ.jpg'
    cv2.imwrite(temp, template)
    cv2.imwrite(targ, target)
    target = cv2.imread(targ)
    target = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
    target = abs(255 - target)
    cv2.imwrite(targ, target)
    target = cv2.imread(targ)
    template = cv2.imread(temp)
    result = cv2.matchTemplate(target, template, cv2.TM_CCOEFF_NORMED)
    x, y = np.unravel_index(result.argmax(), result.shape)
    return x, y
    # # 展示圈出来的区域
    # cv2.rectangle(template, (y, x), (y + w, x + h), (7, 249, 151), 2)
    # cv2.imwrite("yuantu.jpg", template)
    # cv2.imshow('Show', template)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()


def get_track(distance):
    # 模拟轨迹 假装是人在操作
    # 初速度
    v = 0
    # 单位时间为0.2s来统计轨迹，轨迹即0.2内的位移
    t = 0.2
    # 位移/轨迹列表，列表内的一个元素代表0.2s的位移
    tracks = []
    # 当前的位移
    current = 0
    # 到达mid值开始减速
    mid = distance * 7 / 8

    distance += 10  # 先滑过一点，最后再反着滑动回来
    # a = random.randint(1,3)
    while current < distance:
        if current < mid:
            # 加速度越小，单位时间的位移越小,模拟的轨迹就越多越详细
            a = random.randint(2, 4)  # 加速运动
        else:
            a = -random.randint(3, 5)  # 减速运动

        # 初速度
        v0 = v
        # 0.2秒时间内的位移
        s = v0 * t + 0.5 * a * (t ** 2)
        # 当前的位置
        current += s
        # 添加到轨迹列表
        tracks.append(round(s))

        # 速度已经达到v,该速度作为下次的初速度
        v = v0 + a * t

    # 反着滑动到大概准确位置
    for _ in range(4):
        tracks.append(-random.randint(2, 3))
    for _ in range(4):
        tracks.append(-random.randint(1, 3))
    return tracks


def bypass_captcha(driver):
    driver.implicitly_wait(10)
    # 破解滑动验证码
    try:
        # 打开验证码界面
        frame = driver.find_element(By.XPATH, '//*[@id="newVcodeIframe"]/iframe')
        driver.switch_to.frame(frame)
        time.sleep(3)
        logging.info("找到滑动验证码.")

        # 获取图片
        back_pic_element = driver.find_element(By.XPATH, '//img[@id="slideBg"]')
        back_url = back_pic_element.get_attribute('src')
        slide_element = driver.find_element(By.XPATH, '//img[@id="slideBlock"]')
        slide_url = slide_element.get_attribute('src')

        r = requests.get(back_url)
        with open("/tmp/back.png", "wb") as f2:
            f2.write(r.content)
            f2.close()
        r = requests.get(slide_url)
        with open("/tmp/slide.png", "wb") as f2:
            f2.write(r.content)
            f2.close()

        position = (0, 0)
        try:
            position = get_postion("/tmp/back.png", "/tmp/slide.png")
        except Exception as e1:
            logging.error("OpenCV 判断出错: ", e1)

        real_width = Image.open('/tmp/back.png').size[0]
        width_scale = float(real_width) / float(back_pic_element.size['width'])
        real_position = position[1] / width_scale
        real_position -= (slide_element.location['x'] - back_pic_element.location['x'])
        real_position += 1

        print("位移: " + str(real_position))

        # 获得滑块
        # slide = driver.find_element_by_id('tcaptcha_drag_thumb')
        # ActionChains(driver).click_and_hold(slide).perform()
        # ActionChains(driver).move_by_offset(xoffset=real_position, yoffset=0).perform()
        # ActionChains(driver).release(slide).perform()

        track_list = get_track(real_position)

        ActionChains(driver).click_and_hold(
            on_element=driver.find_element(By.ID, 'tcaptcha_drag_thumb')).perform()  # 点击鼠标左键，按住不放
        time.sleep(0.2)
        # print('第二步,拖动元素')
        for track in track_list:
            ActionChains(driver).move_by_offset(xoffset=track, yoffset=0).perform()  # 鼠标移动到距离当前位置（x,y）
            time.sleep(0.002)
        # ActionChains(driver).move_by_offset(xoffset=-random.randint(0, 1), yoffset=0).perform()   # 微调，根据实际情况微调
        time.sleep(1)
        # print('第三步,释放鼠标')
        ActionChains(driver).release(on_element=driver.find_element(By.ID, 'tcaptcha_drag_thumb')).perform()
        time.sleep(1)

    except Exception as e2:
        # 没有验证码
        logging.error(e2)
        logging.info("无验证码或处理验证码时出错: " + str(e2))


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
    with webdriver.Chrome(options=get_chrome_options()) as driver:
        # 登录
        login_timeout = 60

        driver.set_page_load_timeout(login_timeout)
        driver.set_script_timeout(login_timeout)

        if last_cookie:
            driver.get("https://user.qzone.qq.com/404page")
            logging.info("设置上一次登录成功的 Cookie: " + str(last_cookie))
            for ck in last_cookie:
                driver.add_cookie(ck)

        driver.get('https://i.qq.com/')
        driver.implicitly_wait(login_timeout)

        for i2 in range(0, 5):
            time.sleep(1)
            # 当前 cookie 尚未失效, 直接登录
            if "user.qzone.qq.com" in driver.current_url:
                break
        else:
            # 尝试重新登录
            try:
                driver.switch_to.frame('login_frame')
            except:
                # 这里一直出错, 打印出 base64 用于排查
                logging.debug(driver.get_screenshot_as_base64())

            driver.find_element(By.ID, 'switcher_plogin').click()
            driver.find_element(By.ID, 'u').clear()
            driver.find_element(By.ID, 'u').send_keys(username)
            driver.find_element(By.ID, 'p').clear()
            driver.find_element(By.ID, 'p').send_keys(password)
            time.sleep(1)
            driver.find_element(By.ID, 'login_button').click()
            time.sleep(5)

            bypass_captcha(driver)

            for i2 in range(0, 10):
                time.sleep(1)
                if "user.qzone.qq.com" in driver.current_url:
                    break
            else:
                raise Exception("登录失败! 用户名或密码错误/网络存在风险/需要手机号验证/验证码处理失败")

        return cookie_to_str(driver.get_cookies())


def qr_login():
    with webdriver.Chrome(options=get_chrome_options()) as driver:
        # 登录
        login_timeout = 60

        driver.set_page_load_timeout(login_timeout)
        driver.set_script_timeout(login_timeout)
        driver.get('https://i.qq.com/')
        driver.implicitly_wait(logging)

        driver.switch_to.frame('login_frame')
        b64 = driver.find_element(By.ID, "qrlogin_img").screenshot_as_base64
        print("二维码: " + b64)
        wechat_push_img(b64)

        for i2 in range(0, 120):
            time.sleep(1)
            if "user.qzone.qq.com" in driver.current_url:
                break
        else:
            raise Exception("登录失败! 二维码登录超时!")

        global last_cookie
        last_cookie = driver.get_cookies()

        return cookie_to_str(driver.get_cookies())
