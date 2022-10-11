import pandas as pd
from EC import create_edit_check

file = r"C:\Users\zhuliwei\Desktop\新建 Microsoft Excel 工作表.xlsx"
save = r"C:\Users\zhuliwei\Desktop\DDDD.xlsx"

df = pd.read_excel(file, sheet_name='Sheet3')
df['代码'] = ''
for row in range(df.shape[0]):
    names = str(df.iloc[row, 9])
    codes = str(df.iloc[row, 5])
    visits = str(df.iloc[row, 2])
    pages = str(df.iloc[row, 3])
    fields = str(df.iloc[row, 4])
    notes = str(df.iloc[row, 6])
    df.iloc[row, 12] = create_edit_check(names, codes, visits, pages, fields, notes)

df.to_excel(save, index=False)
