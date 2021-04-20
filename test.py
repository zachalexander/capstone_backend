from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

driver = webdriver.Chrome(ChromeDriverManager(version="87.0.4280.88").install())
driver.get("https://www.google.com")
d = webdriver.Chrome()
d.get('https://www.google.com/get/sunroof/building/34.00192560211979/-81.21430071233021/#?f=buy')
test = [e.text for e in d.find_elements_by_name('.place-map')]
print(test)
# d.close()