#! /usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import random
import numpy as np
from selenium.webdriver.support.ui import Select
import openpyxl
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import NoSuchElementException

import re
data = pd.read_excel(r"/Users/stefan/Desktop/joblab/Poisk.xlsx", engine='openpyxl')
#data = pd.read_excel(r"/Users/allastepannikova/Downloads/Poisk.xlsx", engine='openpyxl')
vac_search = data['vacans'].to_list()
zp = data['zepe'].to_list()
urls = []


for ind,inputting in enumerate(vac_search):
    for cities in range(2):
        url_start = 'https://joblab.ru/search.php'
        browser = webdriver.Chrome()
        #browser = webdriver.Chrome(executable_path=r"/Users/stefan/Desktop/joblab/chromedriver")
        browser.get(url_start)
        searching = browser.find_element(By.XPATH, '/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/form/table/tbody/tr[2]/td[2]/p/input')
        searching.send_keys(inputting)
        iscluchenie = browser.find_element(By.XPATH, '/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/form/table/tbody/tr[4]/td[2]/p/input')
        iscluchenie.send_keys(r'гку фгу гб фб мбу мвд госу федера облас муп гау фау шве одежд продаж')
        zarp_find=browser.find_element(By.XPATH, '/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/form/table/tbody/tr[11]/td[2]/p/input')
        zarp_find.send_keys(zp[ind])
        if cities ==1:
            select = Select(browser.find_element(By.XPATH, '/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/form/table/tbody/tr[6]/td[2]/p/select'))
            select.select_by_visible_text('Санкт-Петербург и область')
        iscluchenie = browser.find_element(By.XPATH, '/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/form/table/tbody/tr[16]/td[2]/p[1]/label/input')
        iscluchenie.click()
        iscluchenie =  browser.find_element(By.XPATH, '/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/form/table/tbody/tr[16]/td[2]/p[3]/label/input')
        iscluchenie.click()
        iscluchenie =  browser.find_element(By.XPATH, '/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/form/table/tbody/tr[16]/td[2]/p[2]/label/input')
        iscluchenie.click()
        searching = browser.find_element(By.XPATH, '/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/form/table/tbody/tr[19]/td[2]/p/input[3]')
        searching.click()
        time.sleep(random.randint(1,2))
        searching = browser.find_element(By.XPATH,'/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/table[2]/tbody/tr/td[1]/p/span[5]/a')
        searching.click()
        time.sleep(2)
        url_current = browser.current_url
        try:
            number_of_pages = int(browser.find_element(By.XPATH, '//a[@title="последняя"]').text)
            print(number_of_pages)
            for page in range(1, number_of_pages+1):
                url_current = browser.current_url
                browser.get(url_current)
                soup = BeautifulSoup(browser.page_source,'html.parser')
                cards = soup.find_all('p', class_="prof")
                for card in cards:
                    url_card = card.find('a', target="_blank").attrs['href']
                    urls.append('https://joblab.ru'+url_card)
                if page==1:
                    next_page = browser.find_element(By.XPATH, '/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/table[4]/tbody/tr/td[1]/p/a')
                else:
                    try:
                        next_page = browser.find_element(By.XPATH, '/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/table[4]/tbody/tr/td[1]/p/a[2]')
                    except:
                        break
                next_page.click()
                time.sleep(3)
            browser.quit()
        except:
            url_current = browser.current_url
            browser.get(url_current)
            soup = BeautifulSoup(browser.page_source,'html.parser')
            cards = soup.find_all('p', class_="prof")
            for card in cards:
                url_card = card.find('a', target="_blank").attrs['href']
                urls.append('https://joblab.ru'+url_card)
            browser.quit()
    
browser = webdriver.Chrome()
for chisl, url in enumerate(urls):
    
    company = []
    fio = []
    phone=[]
    email =[]
    vacancy_name=[]
    place=[]
    money=[]
    urls_itog = []
    browser.get(url)
    vac = browser.find_element(By.XPATH, '/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/h1').text
    vacancy_name.append(vac)
    try:
        tel = browser.find_element(By.XPATH, '/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/table[1]/tbody/tr[3]/td[2]/p/span/a')
        tel.click()
    except:
        tel = None
    try:
        mail = browser.find_element(By.XPATH, '/html/body/table/tbody/tr[2]/td/div/table/tbody/tr/td/table[1]/tbody/tr[4]/td[2]/p/span/a')
        mail.click()
    except:
        mail = None
        
    time.sleep(3)
    soup = BeautifulSoup(browser.page_source,'html.parser')
    table = soup.find('table', class_="table-to-div")
    information = table.find_all('tr')
    for stroka in information:
        both_col = stroka.find_all('td')
        if ('Прямой работодатель' in both_col[0].text):
            compa = both_col[1].text
            indexes = []
            for inde, e in enumerate(compa):
                if e=='"':
                    indexes.append(inde)
            if indexes:
                compa = compa[indexes[0]+1:indexes[1]]
            company.append(compa)
        elif 'Контактное лицо' in both_col[0].text:
            fio.append(both_col[1].text)
        elif 'Телефон' in both_col[0].text:
            tel = 'yes'
            formatt = both_col[1].text
            formatt = formatt.split(', ')
            current = ""
            for el in formatt:
                new = "+7"+el[1:]
                new = new.replace("(", "")
                new = new.replace(")", "")
                new = new.replace(" ", "")
                new = new.replace("-", "")
                new = new[:8] + "-" + new[8:]
                new = new[:2] + "(" + new[2:5] + ")" + new[5:13]
                if len(formatt) > 1:
                    current = new  + ", " + current
                else:
                    current = new
            if len(formatt) > 1:
                current = current[:-2]
            phone.append(current)
        elif 'E-mail' in both_col[0].text:
            mail = 'yes'
            email.append(both_col[1].text)
        elif 'Город' in both_col[0].text:
            gorod = both_col[1].text.replace("   –   на карте", "")
            try:
                index_gor = gorod.index(',')
                gorod = gorod[:index_gor]
            except:
                pass
            place.append(gorod)
        elif 'Заработная плата' in both_col[0].text:
            mon = both_col[1].text.replace(" руб."," RUR")
            money.append(mon)
    if len(fio) != len(phone):
        phone.append('Нет инфо')
    if len(fio) != len(email):
        email.append('Нет инфо')
    urls_itog.append(url)
    try:
        matrix = np.array([company, fio, phone, email, vacancy_name, urls_itog, place, money])
        matrix = matrix.transpose()
        df = pd.DataFrame(data=(matrix), columns=['Компания','ФИО','Телефон','E-mail','Вакансия', 'Ссылка', 'Город','Заработная плата'])
        # здесь путь к результирующему файлу
        file_= r"/Users/stefan/Desktop/joblab/vac.xlsx"
#        file_= r"/Users/allastepannikova/Desktop/vac.xlsx"

#        wb = openpyxl.Workbook()
#        wb.save(file_)
        with pd.ExcelWriter(file_, mode='a', engine="openpyxl",if_sheet_exists='overlay') as writer:
            df.to_excel(writer, sheet_name='Sheet', startrow=chisl+1, index=False, header=False)
    except:
        print(company, fio, phone, email, vacancy_name, urls_itog, place, money)

browser.quit()

