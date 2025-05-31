# -*- coding: utf-8 -*-
import time
from datetime import datetime
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    NoAlertPresentException,
    NoSuchElementException,
    TimeoutException
)
from webdriver_manager.chrome import ChromeDriverManager

from srt_reservation.exceptions import (
    InvalidStationNameError,
    InvalidDateError,
    InvalidDateFormatError
)
from srt_reservation.validation import station_list
from srt_reservation.send_email import send_email


class SRT:
    def __init__(self, dpt_stn, arr_stn, dpt_dt, dpt_tm, start_trains_to_check=1, num_trains_to_check=2, want_reserve=False):
        self.login_id = None
        self.login_psw = None

        self.dpt_stn = dpt_stn
        self.arr_stn = arr_stn
        self.dpt_dt = dpt_dt
        self.dpt_tm = dpt_tm

        self.start_trains_to_check = start_trains_to_check
        self.num_trains_to_check = num_trains_to_check
        self.want_reserve = want_reserve

        self.driver = None

        self.sender = None
        self.recipient = None
        self.app_password = None

        self.is_booked = False
        self.cnt_refresh = 0

        self.check_input()

    def check_input(self):
        if self.dpt_stn not in station_list:
            raise InvalidStationNameError(f"출발역 오류. '{self.dpt_stn}' 은/는 목록에 없습니다.")
        if self.arr_stn not in station_list:
            raise InvalidStationNameError(f"도착역 오류. '{self.arr_stn}' 은/는 목록에 없습니다.")
        if not str(self.dpt_dt).isnumeric():
            raise InvalidDateFormatError("날짜는 숫자로만 이루어져야 합니다.")
        try:
            datetime.strptime(str(self.dpt_dt), '%Y%m%d')
        except ValueError:
            raise InvalidDateError("날짜가 잘못 되었습니다. YYYYMMDD 형식으로 입력해주세요.")

    def set_log_info(self, login_id, login_psw):
        self.login_id = login_id
        self.login_psw = login_psw

    def set_email_info(self, sender=None, recipient=None, app_password=None):
        self.sender = sender
        self.recipient = recipient
        self.app_password = app_password
        if not (self.sender and self.recipient and self.app_password):
            print("이메일 정보가 설정되지 않았습니다.")
            return
        send_email("SRT 매크로 시작", "SRT 매크로가 시작되었습니다.", self.sender, self.recipient, self.app_password)
        print("이메일 정보가 설정되었습니다.")

    def run_driver(self):
        chrome_options = webdriver.ChromeOptions()
        s = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=s, options=chrome_options)

    def login(self):
        self.driver.get('https://etk.srail.co.kr/cmc/01/selectLoginForm.do')

        id_input = self.driver.find_element(By.ID, 'srchDvNm01')
        pw_input = self.driver.find_element(By.ID, 'hmpgPwdCphd01')

        id_input.clear()
        id_input.send_keys(self.login_id)
        pw_input.clear()
        pw_input.send_keys(self.login_psw)

        self.driver.find_element(By.XPATH, '//*[@id="login-form"]/fieldset/div[1]/div[1]/div[2]/div/div[2]/input').click()

        # 로그인 후 명시적 대기 (예: URL 변경 또는 특정 요소 등장 대기)
        # try:
        #     WebDriverWait(self.driver, 10).until(
        #         EC.presence_of_element_located((By.CSS_SELECTOR, "#wrap > div.header.header-e > div.global.clear > div"))

        #         # EC.presence_of_element_located((By.CLASS_NAME, "logout"))  # ← 실제 있는 요소로 바꿔야 함
        #     )
        # except TimeoutException:
        #     print("⚠️ 로그인 후 로딩이 너무 오래 걸립니다.")


    def check_login(self):
        try:
            # 요소가 나타날 때까지 최대 10초 기다림
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#wrap > div.header.header-e > div.global.clear > div"))
            )
            # 요소가 나타나면 텍스트 검사
            if "환영합니다" in element.text:
                return True
            else:
                return False
        except (NoSuchElementException, TimeoutException):
            return False

    def go_search(self):
        self.driver.get('https://etk.srail.kr/hpg/hra/01/selectScheduleList.do')
        # 명시적으로 해당 요소가 나타날 때까지 최대 10초 대기
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'dptRsStnCdNm'))
        )

        self.driver.find_element(By.ID, 'dptRsStnCdNm').clear()
        self.driver.find_element(By.ID, 'dptRsStnCdNm').send_keys(self.dpt_stn)

        self.driver.find_element(By.ID, 'arvRsStnCdNm').clear()
        self.driver.find_element(By.ID, 'arvRsStnCdNm').send_keys(self.arr_stn)

        Select(self.driver.find_element(By.ID, "dptDt")).select_by_value(self.dpt_dt)
        Select(self.driver.find_element(By.ID, "dptTm")).select_by_visible_text(self.dpt_tm)

        print(f"출발역:{self.dpt_stn} → 도착역:{self.arr_stn} | 날짜:{self.dpt_dt}, {self.dpt_tm}시 이후")
        print(f"확인할 열차 수: {self.num_trains_to_check}, 예약 대기 허용: {self.want_reserve}")

        self.driver.find_element(By.XPATH, "//input[@value='조회하기']").click()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#result-form table tbody tr"))
        )

    def handle_alert_if_present(self):
        try:
            alert = self.driver.switch_to.alert
            print(f"[!] 알림 감지: {alert.text}")
            alert.accept()
            time.sleep(0.5)
        except NoAlertPresentException:
            pass

    def book_ticket(self, seat_text, i):
        if "예약하기" in seat_text:
            btn = self.driver.find_element(By.CSS_SELECTOR,
                f"#result-form tbody tr:nth-child({i}) td:nth-child(7) > a")
            try:
                btn.click()
            except ElementClickInterceptedException:
                btn.send_keys(Keys.ENTER)

            self.handle_alert_if_present()

            if self.driver.find_elements(By.ID, 'isFalseGotoMain'):
                self.is_booked = True
                print("✅ 예약 성공!")
                if self.sender and self.recipient and self.app_password:
                    send_email("SRT 예약 완료", "빨리 결제 하삼.", self.sender, self.recipient, self.app_password)
                return True

            print("⚠️ 예약 실패 또는 잔여석 없음")
        return False

    def reserve_ticket(self, reserve_text, i):
        if "신청하기" in reserve_text:
            print("🕗 예약 대기 신청")
            self.driver.find_element(By.CSS_SELECTOR,
                f"#result-form tbody tr:nth-child({i}) td:nth-child(8) > a").click()
            self.is_booked = True
            return True
        return False

    def refresh_result(self):
        time.sleep(random.uniform(1.0, 2.5))
        for attempt in range(3):
            try:
                submit = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@value='조회하기']"))
                )
                self.driver.execute_script("arguments[0].click();", submit)
                self.cnt_refresh += 1
                print(f"🔄 새로고침 {self.cnt_refresh}회")
                time.sleep(0.3)
                break
            except Exception as e:
                print(f"⚠️ 새로고침 실패: {type(e).__name__}, 재시도 {attempt+1}/3")
                time.sleep(1)

    def check_result(self):
        while not self.is_booked:
            for i in range(self.start_trains_to_check, self.start_trains_to_check + self.num_trains_to_check):
                try:
                    row = self.driver.find_element(By.CSS_SELECTOR, f"#result-form tbody tr:nth-child({i})")
                    seat_text = row.find_element(By.CSS_SELECTOR, "td:nth-child(7)").get_attribute("innerText")
                    reserve_text = row.find_element(By.CSS_SELECTOR, "td:nth-child(8)").get_attribute("innerText")
                except Exception:
                    seat_text, reserve_text = "매진", "매진"

                self.handle_alert_if_present()

                if self.book_ticket(seat_text, i):
                    return
                if self.want_reserve and self.reserve_ticket(reserve_text, i):
                    return

            self.refresh_result()
    def run(self, login_id, login_psw, sender=None, recipient=None, app_password=None):
        self.run_driver()
        time.sleep(random.uniform(1.5, 3.5))  # 랜덤 딜레이

        self.set_log_info(login_id, login_psw)
        self.set_email_info(sender, recipient, app_password)
        self.login()

        if not self.check_login():
            print("❌ 로그인 실패: 아이디 또는 비밀번호를 확인하세요.")
            self.driver.quit()
            return
        time.sleep(random.uniform(1.5, 2.3))  # 랜덤 딜레이
        self.go_search()
        self.check_result()

        if self.is_booked:
            print("🎉 작업 종료: 예약 또는 예약 대기 완료")
        else:
            print("🛑 작업 종료: 예약 실패 또는 중단")

