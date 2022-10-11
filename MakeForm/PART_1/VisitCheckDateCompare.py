import pandas as pd
from datetime import datetime
file = r"C:\Users\zhuliwei\Desktop\MLWY-SXX201601_FormExcel_2.2_20220907 to 申办方.xlsx"  ##################
save = r"C:\Users\zhuliwei\Desktop\RES.xlsx"  ########
# sv1a = pd.read_excel(file, sheet_name='SV1A', usecols=['受试者编号', '数据节', '数据页', '访视日期(SVDAT1)'], keep_default_na=False)  ##################
# sv1b = pd.read_excel(file, sheet_name='SV1', usecols=['受试者编号', '数据节', '数据页', '访视日期(SVDAT1)'], keep_default_na=False)  ##################
# sv = pd.concat([sv1a, sv1b])
sv = pd.read_excel(file, sheet_name='SV', usecols=['受试者编号', '数据节', '数据页', '访视日期'], keep_default_na=False)


def check_date_compare(sheets: list):
    # white_list = ['AE', 'AE2', 'CE1', 'CE2', 'CM1', 'CM2', 'CM3', 'DM', 'DS4', 'EC', 'FA4', 'FA5', 'SV1', 'SV1A', 'SV1B', 'PR', 'MH1', 'MH2', 'MH3']  ##################
    white_list = []
    xie = pd.ExcelWriter(save)
    for sheet in sheets:
        print(sheet)
        if sheet in white_list:
            continue
        form = pd.read_excel(file, sheet_name=sheet, keep_default_na=False)
        for col in list(form.columns):
            if '日期' in col:  ##################
                goal_cols = ['受试者编号', '受试者状态', '数据节', '数据块', '数据页', '行号']  ##################
                goal_cols.append(col)
                
                form = form[goal_cols]
                form = form.loc[form['行号'].astype(str) == '1'].drop(columns=['行号'])  ##################

                form = pd.merge(form, sv, how='left', on=['受试者编号', '数据节'])  ##################
                form['实际检查日期和理论访视日期相差的天数'] = ''  ########
                for row in range(form.shape[0]):
                    act_d = str(form.iloc[row, 5])  ##################索引
                    vis_d = str(form.iloc[row, 7])  ##################索引
                    try:
                        form.iloc[row, 8] = datetime.strptime(act_d, '%Y-%m-%d') - datetime.strptime(vis_d, '%Y-%m-%d')  ##################索引
                    except:
                        form.iloc[row, 8] = 'NA'  ##################索引

                form.to_excel(xie, sheet_name=sheet, index=False)

                break
            else:
                pass
    xie.close()
    

def main():
    all = list(pd.ExcelFile(file).sheet_names)
    check_date_compare(all)


main()
