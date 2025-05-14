# -*- coding: utf-8 -*-
import os
import time
from random import randint
from datetime import datetime
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException, WebDriverException, UnexpectedAlertPresentException
from selenium.webdriver.common.alert import Alert

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

from srt_reservation.exceptions import InvalidStationNameError, InvalidDateError, InvalidDateFormatError, InvalidTimeFormatError
from srt_reservation.validation import station_list

# import winsound
import os

from srt_reservation.send_email import send_email
from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException, NoSuchElementException


# chromedriver_path = r'C:\workspace\chrfomedriver.exe'

class SRT:
    def __init__(self, dpt_stn, arr_stn, dpt_dt, dpt_tm, start_trains_to_check=1, num_trains_to_check=2, want_reserve=False):
        """
        :param dpt_stn: SRT 출발역
        :param arr_stn: SRT 도착역
        :param dpt_dt: 출발 날짜 YYYYMMDD 형태 ex) 20220115
        :param dpt_tm: 출발 시간 hh 형태, 반드시 짝수 ex) 06, 08, 14, ...
        :param num_trains_to_check: 검색 결과 중 예약 가능 여부 확인할 기차의 수 ex) 2일 경우 상위 2개 확인
        :param want_reserve: 예약 대기가 가능할 경우 선택 여부
        """
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

        self.is_booked = False  # 예약 완료 되었는지 확인용
        self.cnt_refresh = 0  # 새로고침 회수 기록

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
        if not self.sender or not self.recipient or not self.app_password:
            print("이메일 정보가 설정되지 않았습니다. 이메일을 보내려면 sender, recipient, app_password를 설정하세요.")
            return
        # # 테스트
        send_email("SRT 매크로 시작", "SRT 매크로가 시작되었습니다.", self.sender, self.recipient, self.app_password)
        print("이메일 정보가 설정되었습니다.")

    def run_driver(self):
        # try:
        #     self.driver = webdriver.Chrome(executable_path=chromedriver_path)
        # except WebDriverException:
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument("headless")
        s = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=s, options=chrome_options)
        # self.driver = webdriver.Chrome(ChromeDriverManager().install())

    def login(self):
        self.driver.get('https://etk.srail.co.kr/cmc/01/selectLoginForm.do')
        self.driver.implicitly_wait(15)
        self.driver.find_element(By.ID, 'srchDvNm01').send_keys(str(self.login_id))
        self.driver.find_element(By.ID, 'hmpgPwdCphd01').send_keys(str(self.login_psw))
        self.driver.find_element(By.XPATH, '//*[@id="login-form"]/fieldset/div[1]/div[1]/div[2]/div/div[2]/input').click()
        self.driver.implicitly_wait(5)
        return self.driver

    def check_login(self):
        menu_text = self.driver.find_element(By.CSS_SELECTOR, "#wrap > div.header.header-e > div.global.clear > div").text
        if "환영합니다" in menu_text:
            # while time.time() - start_time < 3:
            #     sound_path = os.path.join(os.environ['SystemRoot'], 'Media', 'Windows Ding.wav')
            #     winsound.PlaySound(sound_path, winsound.SND_FILENAME)         
            return True
        else:
            return False

    def go_search(self):
        # 기차 조회 페이지로 이동
        self.driver.get('https://etk.srail.kr/hpg/hra/01/selectScheduleList.do')
        self.driver.implicitly_wait(5)

        # 출발지 입력
        elm_dpt_stn = self.driver.find_element(By.ID, 'dptRsStnCdNm')
        elm_dpt_stn.clear()
        elm_dpt_stn.send_keys(self.dpt_stn)

        # 도착지 입력
        elm_arr_stn = self.driver.find_element(By.ID, 'arvRsStnCdNm')
        elm_arr_stn.clear()
        elm_arr_stn.send_keys(self.arr_stn)

        # 출발 날짜 입력
        elm_dpt_dt = self.driver.find_element(By.ID, "dptDt")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_dpt_dt)
        Select(self.driver.find_element(By.ID, "dptDt")).select_by_value(self.dpt_dt)

        # 출발 시간 입력
        elm_dpt_tm = self.driver.find_element(By.ID, "dptTm")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_dpt_tm)
        Select(self.driver.find_element(By.ID, "dptTm")).select_by_visible_text(self.dpt_tm)

        print("기차를 조회합니다")
        print(f"출발역:{self.dpt_stn} , 도착역:{self.arr_stn}\n날짜:{self.dpt_dt}, 시간: {self.dpt_tm}시 이후\n{self.num_trains_to_check}개의 기차 중 예약")
        print(f"예약 대기 사용: {self.want_reserve}")

        self.driver.find_element(By.XPATH, "//input[@value='조회하기']").click()
        WebDriverWait(self.driver, 1000).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div/div[4]/div/div[3]/div[1]/form/fieldset/div[6]/table/tbody/tr[1]/td[7]/a'))
        )
        # self.driver.implicitly_wait(5)
        # time.sleep(1)

    def book_ticket(self, standard_seat, i):
        # standard_seat는 일반석 검색 결과 텍스트
            
        if "예약하기" in standard_seat:

            # Error handling in case that click does not work
            try:
                self.driver.find_element(By.CSS_SELECTOR,
                                         f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(7) > a").click()
                try:
                    alert = self.driver.switch_to.alert
                    print(f"[!] 예약 전 알림창 감지: {alert.text}")
                    alert.accept()
                    time.sleep(1)  # 알림창 닫은 후 안정성을 위해 대기
                except:
                    pass  # 알림창이 없으면 그냥 넘어감
            except ElementClickInterceptedException as err:
                print(err)
                self.driver.find_element(By.CSS_SELECTOR,
                                         f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(7) > a").send_keys(
                    Keys.ENTER)
            finally:
                print("예약 가능 클릭")
                self.driver.implicitly_wait(3)
            
            try:
                alert = self.driver.switch_to.alert
                print("Alert 발견:", alert.text)
                alert.accept()  # 확인 누르기
                print("Alert 수락 완료")
            except NoAlertPresentException:
                pass  # Alert 없으면 무시

            # 예약이 성공하면
            if self.driver.find_elements(By.ID, 'isFalseGotoMain'):
                self.is_booked = True
                print("예약 성공")
                import time
                start_time = time.time()
                
                # sound_path = os.path.join(os.environ['SystemRoot'], 'Media', 'Windows Ding.wav')
                # winsound.PlaySound(sound_path, winsound.SND_FILENAME)
                if self.sender and self.recipient and self.app_password: 
                    send_email("SRT 예약 완료", "빨리 결제 하삼.", self.sender, self.recipient, self.app_password)
                return self.driver
            else:
                print("잔여석 없음. 다시 검색")
                self.driver.back()  # 뒤로가기
                self.driver.implicitly_wait(5)
        return False

    # def refresh_result(self):
    #     submit = self.driver.find_element(By.XPATH, "//input[@value='조회하기']")
    #     self.driver.execute_script("arguments[0].click();", submit)
    #     self.cnt_refresh += 1
    #     print(f"새로고침 {self.cnt_refresh}회")
    #     self.driver.implicitly_wait(10)
    #     time.sleep(0.5)
    def refresh_result(self):
        for attempt in range(3):
            try:
                wait = WebDriverWait(self.driver, 10)
                submit = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@value='조회하기']")))
                self.driver.execute_script("arguments[0].click();", submit)
                self.cnt_refresh += 1
                print(f"새로고침 {self.cnt_refresh}회")
                time.sleep(0.5)
                break
            except StaleElementReferenceException:
                print(f"[조회하기 클릭] StaleElement 발생, 재시도 {attempt+1}/3")
                time.sleep(1)
            except NoSuchElementException:
                print(f"[조회하기 클릭] 요소를 찾을 수 없습니다. 재시도 {attempt+1}/3")
                time.sleep(1)
            except TimeoutException:
                print(f"[조회하기 클릭] 요소 로딩 시간 초과. 재시도 {attempt+1}/3")
                time.sleep(1)


    def reserve_ticket(self, reservation, i):
        if "신청하기" in reservation:
            print("예약 대기 완료")
            self.driver.find_element(By.CSS_SELECTOR,
                                     f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(8) > a").click()
            self.is_booked = True
            return self.is_booked

    def check_result(self):
        while True:
            for i in range(self.start_trains_to_check, self.start_trains_to_check + self.num_trains_to_check):
                try:
                    standard_seat = self.driver.find_element(By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(7)").text
                    reservation = self.driver.find_element(By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(8)").text
                except StaleElementReferenceException:
                    standard_seat = "매진"
                    reservation = "매진"
                # 🔹 알림창이 떠 있으면 먼저 닫아줌
                try:
                    alert = self.driver.switch_to.alert
                    print(f"[!] 예약 전 알림창 감지: {alert.text}")
                    alert.accept()
                    time.sleep(1)  # 알림창 닫은 후 안정성을 위해 대기
                except:
                    pass  # 알림창이 없으면 그냥 넘어감

                # try:
                #     if self.book_ticket(standard_seat, i):
                #         return self.driver
                # except UnexpectedAlertPresentException:
                #     alert = self.driver.switch_to.alert
                #     print(f"[!] 예약 중 알림창 감지: {alert.text}")
                #     alert.accept()  # 알림창 확인 버튼 클릭
                #     time.sleep(1)  # 알림창을 닫고 안정성을 위해 대기 후 다시 시도
                #     continue  # 다음 루프에서 다시 시도

                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException

                try:
                    if self.book_ticket(standard_seat, i):
                        return self.driver
                except UnexpectedAlertPresentException:
                    print("[!] UnexpectedAlertPresentException 발생 — alert 처리 시도")
                    try:
                        WebDriverWait(self.driver, 2).until(EC.alert_is_present())
                        alert = self.driver.switch_to.alert
                        print(f"[!] 예약 중 알림창 감지: {alert.text}")
                        alert.accept()
                        time.sleep(1)
                    except NoAlertPresentException:
                        print("Alert 확인 중 NoAlertPresentException: 이미 닫혔을 수도 있음")
                    except Exception as e:
                        print("Alert 처리 중 기타 오류:", e)
                    # 예약 재시도는 필요하면 외부 루프에서 처리


                if self.want_reserve:
                    self.reserve_ticket(reservation, i)

            if self.is_booked:
                return self.driver

            else:
                time.sleep(randint(2, 4))
                self.refresh_result()

    def run(self, login_id, login_psw, sender=None, recipient=None, app_password=None):
        self.run_driver()
        self.set_log_info(login_id, login_psw)
        self.set_email_info(sender, recipient, app_password)
        self.login()
        # sound_path = os.path.join(os.environ['SystemRoot'], 'Media', 'Windows Ding.wav')
        # winsound.PlaySound(sound_path, winsound.SND_FILENAME)        
        self.go_search()
        self.check_result()

#
# if __name__ == "__main__":
#     srt_id = os.environ.get('srt_id')
#     srt_psw = os.environ.get('srt_psw')
#
#     srt = SRT("동탄", "동대구", "20220917", "08")
#     srt.run(srt_id, srt_psw)

