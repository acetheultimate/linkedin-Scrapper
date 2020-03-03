#!/usr/bin/env python
import os
import sys
import time
import random
import shelve
import getpass
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC

FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('LinkedInScrapper')
logger.setLevel(logging.INFO)


class LinkedInScrapper:
    def __init__(self, driver_path="./chromedriver", input_fp="", output_fp=sys.stdout):
        self.input_fp = input_fp
        self.output_fp = output_fp
        proxy_add, user_agent = self.generate_user_agent_and_proxy()
        service_args = [
            '--proxy=%s' % proxy_add,
            '--proxy-type=http',
            '--ssl-protocol=any',
            '--ignore-ssl-errors=true'
        ]

        # opts = webdriver.ChromeOptions()
        opts = webdriver.FirefoxOptions()
        opts.add_argument("--user-agent=%s" % user_agent)
        # self.driver = webdriver.Chrome(executable_path=driver_path,
        #                                service_args=service_args,
        #                                chrome_options=opts)
        self.driver = webdriver.Firefox()
        self.driver.set_window_size(1366, 768)

        self.sign_in = False

    def signIn(self):
        # id_ = input("Enter you LinkedIn ID: ")
        # pass_ = getpass.getpass("Enter your password: ")
        id_ = "ankitdogra1996@gmail.com"
        pass_ = "Linkedinkapassword."
        self.driver.get("https://www.linkedin.com/")

        # try:
        #     WebDriverWait(self.driver, 10).until(
        #         # EC.presence_of_element_located((By.ID, "login-email"))
        #           EC.presence_of_element_located((By.CLASS_NAME,"sign-in-card show"))
        #     )
        # except TimeoutException:
        #     print("Unable to login! Please report!")
        #     return False
        time.sleep(4)
        self.driver.find_element_by_xpath("//form/div[1]/div[1]/input").send_keys(id_)
        self.driver.find_element_by_xpath("//form/div[1]/div[2]/input").send_keys(pass_)
        self.driver.find_element_by_class_name("sign-in-form__submit-btn").click()
        # self.driver.find_element_by_id("login-email").send_keys(id_)
        # self.driver.find_element_by_id("login-password").send_keys(pass_)
        # self.driver.find_element_by_id("login-submit").click()
        return True

    def scrapper(self, linkedin):
        logger.info("Looking for " + linkedin)
        linkedin = linkedin.strip()
        logger.info("Opening " + linkedin)
        self.driver.execute_script('window.location.href = "%s"' % linkedin)
        logger.info("Opened!")
        # soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        # print(soup)
        # Declaration of variables needed
        out_dict = {"name": None,
                    "email": None,
                    "phone": None,
                    "company": None,
                    "designation": None,
                    "location": None}
        try:
            # out_dict["name"] = WebDriverWait(self.driver, 10).until(
            #     EC.presence_of_element_located((By.XPATH, "//section/div[2]/div[2]/div[1]/ul[1]/li[1]"))
            # ).text

            # out_dict["name"] = element.find_element_by_class_name("inline t-24 t-black t-normal break-words").text.strip()
            # time.sleep(4)
            out_dict["name"] = self.driver.find_element_by_xpath("//section/div[2]/div[2]/div[1]/ul[1]/li[1]").text.strip()
            out_dict["location"] = self.driver.find_element_by_xpath("//section/div[2]/div[2]/div[1]/ul[2]/li[1]").text.strip()

            try:
                out_dict["company"] = self.driver.find_element_by_class_name("mt1 t-18 t-black t-normal").text.strip()
            except NoSuchElementException:
                out_dict["company"] = ""
            if out_dict["company"] == "":
                try:

                    out_dict["company"] = [i.strip() for i in
                               self.driver.find_element_by_xpath("//section/div[2]/div[2]/div[1]/h2").text.split(" at ")][1]
                except IndexError:
                    out_dict["company"] = ""
            try:
                out_dict["designation"] = [i.strip() for i in self.driver.find_element_by_xpath("//section/div[2]/div[2]/div[1]/h2").text.split(" at ")][0]
            except ValueError:
                out_dict["designation"] = self.driver.find_element_by_xpath("//section/div[2]/div[2]/div[1]/h2").text.strip()

            try:
                # WebDriverWait(self.driver, 10).until(
                #     EC.presence_of_element_located((By.XPATH, "/html/body/div[6]/div[4]/div[3]/div/div/div/div/div[2]/main/div[1]/section/div[2]/div[2]/div[1]/ul[2]/li[3]/a/span"))
                # ).click()


                self.driver.find_element_by_xpath("//section/div[2]/div[2]/div[1]/ul[2]/li[3]/a/span").click()
            except Exception as e:
                print("Error while fetching more details")
                print(e)

            try:
                out_dict["email"] = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//section[@class='pv-contact-info__contact-type ci-email']/div"))
                ).text
                out_dict["phone"] = self.driver.find_element_by_class_name("//section[@class='pv-contact-info__contact-type ci-phone']/ul/li/span[1]").text

            except Exception as e:
                logger.warning("Error while fetching more details." + str(e))

            return out_dict

        except Exception as e:
            print("Error while scraping!", e)
            print("Output so far ", out_dict)
            return False

    def begin(self):
        """
        Function that contains input and output file.
        :return:
        """
        sign_in = input("Do you want to sign in?(Limited information for guest) (y/n): ")
        if sign_in == 'y' or sign_in == 'Y':
            sign_in = self.signIn()
        else:
            sign_in = False

        if not sign_in:
            continue_as_guest = input("You are not logged in! Want to continue as guest?(y/n): ")
            if continue_as_guest == 'y' or continue_as_guest == 'Y':
                pass
            else:
                print("Exiting!")
                return

        dp = False

        try:
            from tabulate import tabulate
        except ImportError:
            print("Tabulate not found, Please install it by using `pip install tabulate`!")
            dp = input("Want to continue with dirty print? (y/n): ")
            if dp == 'y' or dp == 'Y':
                dp = True
                pass
            else:
                return

        if not dp: # Pretty print is requested
            if self.output_fp != sys.stdout: # Check if we are printing in a file
                if not os.path.isfile(self.output_fp):
                    # check if file is not present
                    # initialize with Pretty print headings
                    with open(self.output_fp, 'w') as f:
                        init_ = tabulate([['', '', '', '', '', '']],
                                         headers=['name', 'email', 'phone', 'company', 'desig', 'location'],
                                         tablefmt="html")

                        f.write(init_.split("<tbody>")[0]+"<tbody>")

        # Let the crawling begin!
        with open(self.output_fp, "w") as f:
            for url in enumerate(open(self.input_fp).readlines()):
                out_ = self.scrapper(url[1])
                if out_:
                    logger.info("Request Completed for " + url[1] + " at " + str(url[0]))
                    print(out_)
                    fout_ = dict([i, [out_[i]]] for i in out_)
                    _ = tabulate(fout_, tablefmt="html").split("tbody")
                    f.write(_[1][1:-2])

                else:
                    continue_ = input("Some error at " + str(url[0]) + ". Want to continue? (y/n): ")
                    if continue_ == 'y' or continue_ == 'Y':
                        continue
                    else:
                        print("Exiting")
                        return

    @staticmethod
    def data(operation, **kwargs):
        """
        :param operation: [int] 0 for reading the data
                          1 for writing new data replacing old
                          2 for append in existing(to depth 1, else overwrite),
                            if not present same as writing new
                          3 render db
        :param kwargs: [dict] key(s) and value(s)
                       For reading, {"key_list": [list] key(s)}
                       For writing, {"key1": value, "key2": value ...}
        :returns: [dict] or [boolean] corresponding to read or write's success
        :rtype: dict or bool
        """

        if not (0 <= operation <= 3):
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

    @staticmethod
    def generate_user_agent_and_proxy():
        """
        Generates tuple for proxy and user-agent respectively
        :rtype: tuple
        """
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
            # "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9",
            ]

        return random.choice(pl), random.choice(user_agents)


obj = LinkedInScrapper(input_fp="/home/webmob/Desktop/file.txt", output_fp="/home/webmob/Desktop/file2.txt")
obj.begin()
