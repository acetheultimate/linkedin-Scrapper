import time
import json
import random
import shelve
import getpass
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC

class LinkedInScrapper:
    def __init__(self, driver_path="./chromedriver", input_fp="", output_fp=""):
        self.input_fp = input_fp
        self.output_fp = output_fp
        proxy_add, user_agent = self.generate_user_agent_and_proxy()
        driver_path = "./chromedriver"
        service_args = [
            '--proxy=%s' % proxy_add,
            '--proxy-type=http',
            '--ssl-protocol=any',
            '--ignore-ssl-errors=true'
        ]

        opts = webdriver.ChromeOptions()
        opts.add_argument("--user-agent=%s" % user_agent)
        self.driver = webdriver.Chrome(executable_path=driver_path,
                                       service_args=service_args,
                                       chrome_options=opts)

        self.driver.set_window_size(1366, 768)

    def generate_user_agent_and_proxy(self):
        pl = ['188.32.106.120:8081',
              '95.79.41.94:8081',
              '188.255.29.89:8081',
              '195.123.209.104:80',
              '36.67.50.242:8080',
              '36.228.41.168:8888',
              '175.139.65.229:8080',
              '187.87.77.76:3128',
              '223.19.210.69:80',
              '91.205.52.234:8081']
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1"]

        return random.choice(pl), random.choice(user_agents)

    def signIn(self):
        self.driver.get("https://www.linkedin.com/mynetwork/invite-connect/connections/")
        frame = self.driver.find_element_by_class_name("authentication-iframe")
        self.driver.switch_to.frame(frame)
        self.driver.find_element_by_class_name("sign-in-link").click()
        self.driver.find_element_by_id("session_key-login").send_keys(input("Enter you LinkedIn ID: "))
        self.driver.find_element_by_id("session_password-login").send_keys(getpass.getpass("Enter your password: "))
        self.driver.find_element_by_id("btn-primary").click()
        time.sleep(5)

    def scrapper(self, linkedin, nr, driver):
        linkedin = linkedin.strip()
        print("Opening ", linkedin)
        self.driver.execute_script('window.location.href = "%s"' % linkedin)
        print("Opened!")

        print("souping it up!")
        # soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # Declaration of variables needed
        out_dict = {"name": None,
                    "email": None,
                    "phone": None,
                    "company": None,
                    "desig": None,
                    "location": None}
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pv-top-card-section__body"))
            )
            name = element.find_element_by_class_name("pv-top-card-section__name").text.strip()
            location = element.find_element_by_class_name("pv-top-card-section__location").text.strip()
            try:
                company = element.find_element_by_class_name("pv-top-card-section__company").text.strip()
            except NoSuchElementException:
                company = ""

            if company == "":
                try:
                    company = [i.strip() for i in
                               element.find_element_by_class_name("pv-top-card-section__headline").text.split(" at ")][1]
                except IndexError:
                    company = ""
            try:
                desig = \
                [i.strip() for i in element.find_element_by_class_name("pv-top-card-section__headline").text.split(" at ")][
                    0]
            except ValueError:
                desig = element.find_element_by_class_name("pv-top-card-section__headline").text.strip()
            try:
                email = element.find_element_by_class_name("pv-contact-info__contact-item").text.strip()
            except NoSuchElementException:
                email = None
            #     try:
            #         phone = driver.find_element_by_class_name("ci-phone").find_element_by_class_name("pv-contact-info__contact-item").text.strip()
            #         phone = phone.split("(")[0].strip()
            #     except NoSuchElementException:
            #         print("Phone is not there")
            #         phone = ''

            nr += 1
            for i in out_dict:
                out_dict[i] = eval(i)
            return out_dict
        except:
            return False

    def data(self, operation, **kwargs):
        """
        :param operation: [int] 0 for reading the data
                          1 for writing new data replacing old
                          2 for append in existing(to depth 1, else overwrite),
                            if not present same as writing new
                          3 render db
        :param kwargs: [dict] key(s) and value(s)
                       For reading, {"key_list": [list] key(s)}
                       For writing, {"key1": value, "key2": value ...}
        :return: [dict] or [boolean] corresponding to read or write's success
        """

        if operation == 0 or operation == 1 or operation == 2 or operation == 3:
            pass
        else:
            return False

        with shelve.open("data.db") as f:
            try:
                if operation == 0:
                    out_dict = dict()
                    for i in kwargs["key_list"]:  # Getting keys to be fetched from db
                        if i in f:  # if key exists in db
                            out_dict = f[i]
                        else:
                            out_dict = False

                    return out_dict

                elif operation == 1:
                    for i in kwargs:
                        f[i] = kwargs[i] if isinstance(kwargs[i], (list, dict)) else [kwargs[i]]
                        f.sync()
                    return True

                elif operation == 2:
                    for i in kwargs:
                        if i in f:
                            if isinstance(f[i], list):
                                f[i] = f[i] + kwargs[i] if isinstance(kwargs[i], list) else [kwargs[i]]
                                f.sync()
                            elif isinstance(f[i], dict):
                                f[i] = kwargs[i]
                                f.sync()

                    return True

                elif operation == 3:
                    return dict(f.items())

            except Exception as e:
                print("Error", e)
                return False

    def begin(self):
        """
        Function that contains input and output file.
        :return:
        """
        for url in enumerate(open("raw_out.txt").readlines()):
            out_ = scrapper(url[1], url[0], driver)
            if out_:
                print("Request Completed for", url[1], "at", url[0])

            else:
                print("Some error at", url[0])
                continue


begin(driver)
driver.quit()
