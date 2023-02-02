from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


driver = webdriver.Chrome(ChromeDriverManager().install())
driver.get("https://www.xe.com/currency/")
elements = driver.find_elements(By.CLASS_NAME, 'currency__ListLink-sc-1xymln9-6')
with open("currency_list.txt", "w") as f:
    for element in elements:
        f.write(element.text)
        f.write('\n')