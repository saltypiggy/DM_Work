import pyautogui
import pyperclip
import time
import pandas as pd
#time.sleep(2)
#print(pyautogui.position())


def create(function_name, code, delay):
    pyautogui.moveTo(1853, 131)  # 点击‘添加自定义功能’
    time.sleep(delay)
    pyautogui.click()
    time.sleep(delay)
    pyautogui.moveTo(236, 200)  # 点击‘函数名’
    time.sleep(delay)
    pyautogui.click()
    time.sleep(delay)
    pyperclip.copy(function_name)
    time.sleep(delay)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(delay)

    pyautogui.moveTo(146, 290)  # 点击‘代码’
    pyautogui.click()
    time.sleep(delay)
    pyautogui.click()  # 选中所有区域
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(delay)
    pyperclip.copy(code)
    pyautogui.hotkey('ctrl', 'v')  # 粘贴代码
    time.sleep(delay)
    pyautogui.moveTo(1881, 1012)  # 完成后退出
    pyautogui.click()
    time.sleep(2)


def copy_func_name():
    df = pd.read_excel(r"C:\Users\zhuliwei\Desktop\RES.xlsx", sheet_name = 'Sheet1')
    return list(df['name']), list(df['code'])


def main():
    names = copy_func_name()[0]
    codes = copy_func_name()[1]
    for n, c in zip(names, codes):
        create(n, c, 0.5)


main()
