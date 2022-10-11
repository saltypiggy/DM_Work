import pyautogui
import pyperclip
import time
import pandas as pd
print(pyautogui.position())


def create(function_name, code, delay):
    pyautogui.moveTo(1870, 183)
    time.sleep(delay)
    pyautogui.click()
    time.sleep(delay)
    pyautogui.moveTo(930, 250)
    time.sleep(delay)
    pyautogui.click()
    time.sleep(delay)
    pyperclip.copy(function_name)
    time.sleep(delay)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(delay)
    pyautogui.moveTo(1177, 412)
    time.sleep(delay)
    pyautogui.click()
    time.sleep(delay)

    pyautogui.moveTo(1887, 265)  # 点进去
    pyautogui.click()
    time.sleep(delay)
    pyautogui.click()  # 选中所有区域
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(delay)
    pyperclip.copy(code)
    pyautogui.hotkey('ctrl', 'v')  # 粘贴代码
    time.sleep(delay)
    pyautogui.moveTo(1876, 1011)  # 完成后退出
    pyautogui.click()
    time.sleep(delay)


def copy_func_name():
    df = pd.read_excel(r"C:\Users\zhuliwei\Desktop\DDDD.xlsx", sheet_name = 'Sheet1')
    return list(df['逻辑核查编号']), list(df['代码'])


def main():
    names = copy_func_name()[0]
    codes = copy_func_name()[1]
    for n, c in zip(names, codes):
        create(n, c, 0.4)


main()
