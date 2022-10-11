from 隐藏字段 import hide
import pandas as pd

df = pd.read_excel(r"C:\Users\zhuliwei\Desktop\隐藏.xlsx", sheet_name='Sheet1')
save = r"C:\Users\zhuliwei\Desktop\RES.xlsx"

forms = list(set(df['FormOID']))

code_res = []
fun_name = []

for form in forms:
    part = df.loc[df['FormOID'] == form]
    func_name = str(part.iloc[0, 0])
    show_list = list(part['VariableNo'])  # 得用字段名，因为标签也算，下次记得改
    hide_list = list(part['VariableNo'])
    if str(part.iloc[0, 2]) == 'F':
        show_num = 2
        hide_num = 1
    else:
        show_num = 1
        hide_num = 2
    step_code = hide(func_name, show_list, hide_list, show_num, hide_num)
    code_res.append(step_code)
    fun_name.append(func_name)

res_df = pd.DataFrame({'name': fun_name, 'code': code_res})
res_df.to_excel(save, index=False)
