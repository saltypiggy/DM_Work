import re
import time
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import jieba
import math
ST = time.localtime()
today = '{}-{:02d}-{:02d}'.format(ST[0], ST[1], ST[2])


def checker(sub_id='受试者编号'):  # 一些横向拼接的表，受试者编号列会重复出现，但是第二次read_excel()时，重复col会自动标记.1 .2 .3这样子
    win = tk.Tk()
    win.withdraw()
    ed_path = filedialog.askopenfilename()
    cd_path = filedialog.askopenfilename()
    save_path = filedialog.askdirectory() + '/' + str(cd_path).strip('.xlsx').split('/')[-1] + '_变化部分.xlsx'

    xie = pd.ExcelWriter(save_path)
    for sh_name in pd.ExcelFile(cd_path).sheet_names:
        early_df = pd.read_excel(ed_path, sheet_name = sh_name)
        current_df = pd.read_excel(cd_path, sheet_name = sh_name)

        names_early = sorted(set(early_df[sub_id]))
        names_current = sorted(set(current_df[sub_id]))
        changed_df = pd.DataFrame()
        for nc in names_current:
            p_current = current_df.loc[current_df[sub_id] == nc]
            if nc in names_early:
                p_early = early_df.loc[early_df[sub_id] == nc]
                if p_current.equals(p_early) is False:
                    changed_df = pd.concat([changed_df, p_current])
                else:
                    pass
            else:
                changed_df = pd.concat([changed_df, p_current])
        changed_df.to_excel(xie, sheet_name = sh_name+'之变化部分', index=False)
    xie.close()


# 默认关系是 由描述（左边）到疾病（右边），如果颠倒，请考虑turn_date=True
# 匹配参数建议为0.01
# 以new_301和new_302为永久示例
def like_match(df1, open_txt_col, st1_col_str, ed1_col_str, df2, to_be_matched_col, st2_col_str, ed2_col_str, turn_date=False, match_degree = 0.5, pattern = 1):  # 文本相似度比对的应用
    """
    不含标点，如果zero_cnt为0，判断为描述漏记
	不含标点，如果zero_cnt不为0，匹配等级最高的，在判断日期关系是否合理（”是“/”否“）
	含标点的最简单的拼表看
    """
    open_txt_col_idx = list(df1.columns).index(open_txt_col)
    to_be_matched_col_idx = list(df2.columns).index(to_be_matched_col)
    st1_col_idx = list(df1.columns).index(st1_col_str)
    ed1_col_idx = list(df1.columns).index(ed1_col_str)
    st2_col_idx = list(df2.columns).index(st2_col_str) + df1.shape[1]
    ed2_col_idx = list(df2.columns).index(ed2_col_str) + df1.shape[1]
    if pattern == 1:  # 区分标点符号
        names = sorted(set(df1['受试者编号']))
        df1_lose = pd.DataFrame()
        df_most_like = pd.DataFrame()
        df1_dot = pd.DataFrame()
        for n in names:
            pdf1 = df1.loc[df1['受试者编号'] == n].reset_index(drop=True)
            pdf2 = df2.loc[df2['受试者编号'] == n].reset_index(drop=True)
            pdf1_lose_rows = []  # zero_cnt为0的row1s
            pdf_most_like_rows = [[], []]  # 最匹配的row1s和row2s
            pdf1_dot_rows = []  # 开放文本含有标点的row1s

            for row1 in range(pdf1.shape[0]):  # 根据有无标点进行区分
                open_txt = str(pdf1.iloc[row1, open_txt_col_idx])
                dot_check = re.findall(r'\W+', open_txt, re.DOTALL)
                if len(dot_check) == 0:  # 不含标点
                    zero_cnt = 0
                    max_row_store = []  # 相似超过match_degree的行号row2
                    for row2 in range(pdf2.shape[0]):  # 遍历pdf2每一行，调整zero_cnt 和 max_row_store的值
                        to_be_matched = str(pdf2.iloc[row2, to_be_matched_col_idx])
                        like_dgree = Likelihood().likelihood(open_txt, to_be_matched)
                        if like_dgree is None:  # 防止“异常有临床意义()”为空时的报错
                            like_dgree = 0
                        else:
                            like_dgree = like_dgree
                        if like_dgree < match_degree:
                            pass
                        else:
                            zero_cnt += 1
                            max_row_store.append(row2)

                    if zero_cnt == 0:  # 不含标点，如果zero_cnt为0，判断为描述漏记
                        pdf1_lose_rows.append(row1)
                    else:  # 不含标点，如果zero_cnt不为0，匹配等级最高的，在判断日期关系是否合理（”是“/”否“）
                        pdf_most_like_rows[0] += [row1]*len(max_row_store)
                        pdf_most_like_rows[1] += max_row_store
                else:  # 含标点的最简单的拼表看
                    pdf1_dot_rows.append(row1)
            
            pdf1_lose = pdf1.iloc[pdf1_lose_rows, :]
            pdf1_lose = pd.concat([pdf1_lose, pdf2], axis=1)
            for row in range(pdf1_lose.shape[0]):
                if str(pdf1_lose.iloc[row, 0]) == 'nan' or str(pdf1_lose.iloc[row, 0]) == '':
                    pdf1_lose.iloc[row, 0] = pdf1_lose.iloc[row-1, 0]
                    pdf1_lose.iloc[row, 1] = pdf1_lose.iloc[row-1, 1]
            pdf1_most_like = pdf1.iloc[pdf_most_like_rows[0], :].reset_index(drop=True)
            pdf2_most_like = pdf2.iloc[pdf_most_like_rows[1], :].reset_index(drop=True)
            pdf_most_like = pd.concat([pdf1_most_like, pdf2_most_like], axis=1)
            pdf1_dot = pdf1.iloc[pdf1_dot_rows, :]
            pdf1_dot = pd.concat([pdf1_dot, pdf2], axis=1)
            for row in range(pdf1_dot.shape[0]):
                if str(pdf1_dot.iloc[row, 0]) == 'nan' or str(pdf1_dot.iloc[row, 0]) == '':
                    pdf1_dot.iloc[row, 0] = pdf1_dot.iloc[row-1, 0]
                    pdf1_dot.iloc[row, 1] = pdf1_dot.iloc[row-1, 1]

            df1_lose = pd.concat([df1_lose, pdf1_lose]).dropna(subset=['受试者状态'])
            df_most_like = pd.concat([df_most_like, pdf_most_like])
            df1_dot = pd.concat([df1_dot, pdf1_dot]).dropna(subset=['受试者状态'])

        # 对df_most_like进行日期关系分析
        df_most_like['日期关系是否合理'] = ''
        df_judge_idx = list(df_most_like.columns).index('日期关系是否合理')
        if turn_date is False:
            for row in range(df_most_like.shape[0]):
                left_st = str(df_most_like.iloc[row, st1_col_idx])
                left_ed = str(df_most_like.iloc[row, ed1_col_idx])
                right_st = str(df_most_like.iloc[row, st2_col_idx])
                right_ed = str(df_most_like.iloc[row, ed2_col_idx])
                if DateCheck(right_st, right_ed, left_st, left_ed).fmt_check():
                    if DateCheck(right_st, right_ed, left_st, left_ed).value_check():
                        df_most_like.iloc[row, df_judge_idx] = '是'
                    else:
                        df_most_like.iloc[row, df_judge_idx] = '否'
                else:
                    df_most_like.iloc[row, df_judge_idx] = '本行日期格式错误'
        else:
            for row in range(df_most_like.shape[0]):
                left_st = str(df_most_like.iloc[row, st1_col_idx])
                left_ed = str(df_most_like.iloc[row, ed1_col_idx])
                right_st = str(df_most_like.iloc[row, st2_col_idx])
                right_ed = str(df_most_like.iloc[row, ed2_col_idx])
                if DateCheck(left_st, left_ed, right_st, right_ed).fmt_check():
                    if DateCheck(left_st, left_ed, right_st, right_ed).value_check():
                        df_most_like.iloc[row, df_judge_idx] = '是'
                    else:
                        df_most_like.iloc[row, df_judge_idx] = '否'
                else:
                    df_most_like.iloc[row, df_judge_idx] = '本行日期格式错误'

        return df1_lose, yn_filter(df_most_like, open_txt=open_txt_col), df1_dot, df_most_like
    elif pattern == 2:  # 不区分是否包含标点符号
        names = sorted(set(df1['受试者编号']))
        df1_lose = pd.DataFrame()
        df_most_like = pd.DataFrame()
        #df1_dot = pd.DataFrame()
        for n in names:
            pdf1 = df1.loc[df1['受试者编号'] == n].reset_index(drop=True)
            pdf2 = df2.loc[df2['受试者编号'] == n].reset_index(drop=True)
            pdf1_lose_rows = []  # zero_cnt为0的row1s
            pdf_most_like_rows = [[], []]  # 最匹配的row1s和row2s
            #pdf1_dot_rows = []  # 开放文本含有标点的row1s

            for row1 in range(pdf1.shape[0]):  # 根据有无标点进行区分
                open_txt = str(pdf1.iloc[row1, open_txt_col_idx])
                #dot_check = re.findall(r'\W+', open_txt, re.DOTALL)
                #if len(dot_check) == 0:  # 不含标点
                zero_cnt = 0
                max_row_store = []  # 相似超过match_degree的行号row2
                for row2 in range(pdf2.shape[0]):  # 遍历pdf2每一行，调整zero_cnt 和 max_row_store的值
                    to_be_matched = str(pdf2.iloc[row2, to_be_matched_col_idx])
                    like_dgree = Likelihood().likelihood(open_txt, to_be_matched)
                    if like_dgree is None:  # 防止“异常有临床意义()”为空时的报错
                        like_dgree = 0
                    else:
                        like_dgree = like_dgree
                    if like_dgree < match_degree:
                        pass
                    else:
                        zero_cnt += 1
                        max_row_store.append(row2)
                if zero_cnt == 0:  # 不含标点，如果zero_cnt为0，判断为描述漏记
                    pdf1_lose_rows.append(row1)
                else:  # 不含标点，如果zero_cnt不为0，匹配等级最高的，在判断日期关系是否合理（”是“/”否“）
                    pdf_most_like_rows[0] += [row1]*len(max_row_store)
                    pdf_most_like_rows[1] += max_row_store
                #else:  # 含标点的最简单的拼表看
                    #pdf1_dot_rows.append(row1)
            pdf1_lose = pdf1.iloc[pdf1_lose_rows, :]
            pdf1_lose = pd.concat([pdf1_lose, pdf2], axis=1)
            for row in range(pdf1_lose.shape[0]):
                if str(pdf1_lose.iloc[row, 0]) == 'nan' or str(pdf1_lose.iloc[row, 0]) == '':
                    pdf1_lose.iloc[row, 0] = pdf1_lose.iloc[row-1, 0]
                    pdf1_lose.iloc[row, 1] = pdf1_lose.iloc[row-1, 1]
            pdf1_most_like = pdf1.iloc[pdf_most_like_rows[0], :].reset_index(drop=True)
            pdf2_most_like = pdf2.iloc[pdf_most_like_rows[1], :].reset_index(drop=True)
            pdf_most_like = pd.concat([pdf1_most_like, pdf2_most_like], axis=1)
            # pdf1_dot = pdf1.iloc[pdf1_dot_rows, :]
            # pdf1_dot = pd.concat([pdf1_dot, pdf2], axis=1)
            # for row in range(pdf1_dot.shape[0]):
            #     if str(pdf1_dot.iloc[row, 0]) == 'nan' or str(pdf1_dot.iloc[row, 0]) == '':
            #         pdf1_dot.iloc[row, 0] = pdf1_dot.iloc[row-1, 0]
            #         pdf1_dot.iloc[row, 1] = pdf1_dot.iloc[row-1, 1]

            df1_lose = pd.concat([df1_lose, pdf1_lose]).dropna(subset=['受试者状态'])
            df_most_like = pd.concat([df_most_like, pdf_most_like])
            # df1_dot = pd.concat([df1_dot, pdf1_dot])#.dropna(subset=['受试者状态'])

        # 对df_most_like进行日期关系分析
        df_most_like['日期关系是否合理'] = ''
        df_judge_idx = list(df_most_like.columns).index('日期关系是否合理')
        if turn_date is False:
            for row in range(df_most_like.shape[0]):
                left_st = str(df_most_like.iloc[row, st1_col_idx])
                left_ed = str(df_most_like.iloc[row, ed1_col_idx])
                right_st = str(df_most_like.iloc[row, st2_col_idx])
                right_ed = str(df_most_like.iloc[row, ed2_col_idx])
                if DateCheck(right_st, right_ed, left_st, left_ed).fmt_check():
                    if DateCheck(right_st, right_ed, left_st, left_ed).value_check():
                        df_most_like.iloc[row, df_judge_idx] = '是'
                    else:
                        df_most_like.iloc[row, df_judge_idx] = '否'
                else:
                    df_most_like.iloc[row, df_judge_idx] = '本行日期格式错误'
        else:
            for row in range(df_most_like.shape[0]):
                left_st = str(df_most_like.iloc[row, st1_col_idx])
                left_ed = str(df_most_like.iloc[row, ed1_col_idx])
                right_st = str(df_most_like.iloc[row, st2_col_idx])
                right_ed = str(df_most_like.iloc[row, ed2_col_idx])
                if DateCheck(left_st, left_ed, right_st, right_ed).fmt_check():
                    if DateCheck(left_st, left_ed, right_st, right_ed).value_check():
                        df_most_like.iloc[row, df_judge_idx] = '是'
                    else:
                        df_most_like.iloc[row, df_judge_idx] = '否'
                else:
                    df_most_like.iloc[row, df_judge_idx] = '本行日期格式错误'

        return df1_lose, yn_filter(df_most_like, open_txt=open_txt_col), df_most_like#, df1_dot
    elif pattern == 3:  # 经典in识别模式
        names = sorted(set(df1['受试者编号']))
        lose = pd.DataFrame()
        time = pd.DataFrame()
        fmt = pd.DataFrame()
        time_true = pd.DataFrame()
        for n in names:
            pdf1 = df1.loc[df1['受试者编号'] == n].reset_index(drop=True)
            pdf2 = df2.loc[df2['受试者编号'] == n].reset_index(drop=True)
            t = InCheck(pdf1, pdf2).check_with_date(open_txt_col_idx, st1_col_idx, ed1_col_idx, to_be_matched_col_idx, st2_col_idx-df1.shape[1], ed2_col_idx-df1.shape[1], turn=turn_date)
            time = pd.concat([time, t.time])
            fmt = pd.concat([fmt, t.fmt])
            lose = pd.concat([lose, t.lose])
            time_true = pd.concat([time_true, t.time_true])
        return time, fmt, lose, time_true
    elif pattern == 4:  # 经典issame模式，用于识别 MH#01  AE#01等
        names = sorted(set(df1['受试者编号']))
        lose = pd.DataFrame()
        time = pd.DataFrame()
        fmt = pd.DataFrame()
        time_true = pd.DataFrame()
        for n in names:
            pdf1 = df1.loc[df1['受试者编号'] == n].reset_index(drop=True)
            pdf2 = df2.loc[df2['受试者编号'] == n].reset_index(drop=True)
            t = InCheck(pdf1, pdf2).check_with_date(open_txt_col_idx, st1_col_idx, ed1_col_idx, to_be_matched_col_idx, st2_col_idx-df1.shape[1], ed2_col_idx-df1.shape[1], turn=turn_date, issame=True)
            time = pd.concat([time, t.time])
            fmt = pd.concat([fmt, t.fmt])
            lose = pd.concat([lose, t.lose])
            time_true = pd.concat([time_true, t.time_true])
        return time, fmt, lose, time_true


def yn_filter(most_like_df, name='受试者编号', rep_name='受试者编号 ',
              visit='数据节', rep_visit='数据节 ',
              page='数据页', rep_page='数据页 ',
              open_txt=None,
              date_judge='日期关系是否合理'):  # 配合like_match中1、2模式的most_like板块使用
    old_cols = list(most_like_df.columns)
    if name in old_cols:
        old_cols[old_cols.index(name)] = rep_name
    if visit in old_cols:
        old_cols[old_cols.index(visit)] = rep_visit
    if page in old_cols:
        old_cols[old_cols.index(page)] = rep_page
    
    most_like_df.columns = old_cols
    res = pd.DataFrame()
    names = sorted(set(most_like_df[rep_name]))
    for n in names:
        p1 = most_like_df.loc[most_like_df[rep_name] == n]

        if rep_visit in old_cols:
            visits = sorted(set(p1[rep_visit]))
            for v in visits:
                p2 = p1.loc[p1[rep_visit] == v]
                pages = sorted(set(p2[rep_page]))
                for p in pages:
                    p3 = p2.loc[p2[rep_page] == p]
                    ops = sorted(set(p3[open_txt]))

                    for o in ops:
                        p4 = p3.loc[p3[open_txt] == o]

                        check_date_judges = set(p4[date_judge])
                        if '是' in check_date_judges:
                            pass
                        else:
                            res = pd.concat([res, p4])
        
        else:
            pages = sorted(set(p1[rep_page]))
            for p in pages:
                p3 = p1.loc[p1[rep_page] == p]

                ops = sorted(set(p3[open_txt]))

                for o in ops:
                    p4 = p3.loc[p3[open_txt] == o]

                    check_date_judges = set(p4[date_judge])
                    if '是' in check_date_judges:
                        pass
                    else:
                        res = pd.concat([res, p4])
    return res


class FormatCheck:  # 格式检查
    def __init__(self, sentence, model, long=None):
        self.model = re.compile(model)
        self.sentence = str(sentence)
        if long is None:
            self.long = int(len(self.sentence))
        else:
            self.long = int(long)
        self.result = self.model.findall(self.sentence)

    def check(self):
        try:
            if self.result[0] == '':
                return False
            elif len(self.sentence) == self.long:
                return True
            else:
                return False
        except:
            if len(self.result) == 0:
                return False
            elif len(self.sentence) == self.long:
                return True
            else:
                return False


class DateCheck:  # 4日期逻辑检查
    def __init__(self, ill1, ill2, st, ed=None):
        self.ill1 = str(ill1).strip(' ')
        self.ill2 = str(ill2).strip(' ')
        self.st = str(st).strip(' ')
        if ed is None:
            self.ed = None
        else:
            self.ed = str(ed).strip(' ')

    def fmt_check(self):
        model = re.compile(r'(\d\d\d\d|UK|uk|uK|Uk)-(\d\d|UK|uk|uK|Uk)-(\d\d|UK|uk|uK|Uk)')
        short = ['UK', 'uk', 'uK', 'Uk']
        ed_pos = ['nan', '  ', ' ', 'nannan', '', 'UK', 'uk', 'uK', 'Uk']
        format_tf = True
        if len(model.findall(self.ill1.strip(' '))) == 0 and self.ill1.strip(' ') not in short:
            format_tf = False
        else:
            format_tf = format_tf
        if len(model.findall(self.ill2.strip(' '))) == 0 and self.ill2.strip(' ') not in ed_pos:
            format_tf = False
        else:
            format_tf = format_tf
        if len(model.findall(self.st.strip(' '))) == 0 and self.st.strip(' ') not in short:
            format_tf = False
        else:
            format_tf = format_tf
        if self.ed is None:
            format_tf = format_tf
        elif len(model.findall(self.ed.strip(' '))) == 0 and self.ed.strip(' ') not in ed_pos:
            format_tf = False
        else:
            format_tf = format_tf
        return format_tf

    def value_check(self):
        value_tf = True
        posi = ['nan', '  ', ' ', 'nannan', '']
        if self.ill1 in ['UK', 'uk', 'Uk', 'uK']:
            self.ill1 = 'UK-UK-UK'
        if self.ill2 in posi:
            self.ill2 = today
        elif self.ill2 in ['UK', 'uk', 'Uk', 'uK']:
            self.ill2 = 'UK-UK-UK'
        if self.st in ['UK', 'uk', 'Uk', 'uK']:
            self.st = 'UK-UK-UK'
        if self.ed in posi or self.ed is None:
            self.ed = today
        elif self.ed in ['UK', 'uk', 'Uk', 'uK']:
            self.ed = 'UK-UK-UK'
        self.ill1 = self.ill1.replace('UK', '01').replace('uk', '01').replace('uK', '01').replace('Uk', '01')
        self.ill2 = self.ill2.replace('UK', '31').replace('uk', '31').replace('uK', '31').replace('Uk', '31')
        sstt = self.st.split('-') + self.ill1.split('-')
        for index in range(0, 3):
            if 'UK' in sstt[index] or 'uk' in sstt[index] or 'uK' in sstt[index] or 'Uk' in sstt[index]:
                sstt[index] = sstt[index+3]
        self.st = sstt[0] + '-' + sstt[1] + '-' + sstt[2]
        eedd = self.ed.split('-') + self.ill2.split('-')
        for index in range(0, 3):
            if 'UK' in eedd[index] or 'uk' in eedd[index] or 'uK' in eedd[index] or 'Uk' in eedd[index]:
                eedd[index] = eedd[index+3]
        self.ed = eedd[0] + '-' + eedd[1] + '-' + eedd[2]
        if self.ill1 <= self.st <= self.ed <= self.ill2:
            value_tf = value_tf
        else:
            value_tf = False
        return value_tf

    def value_check_only_st(self):  # if self.ill1 <= self.st <= self.ill2:
        value_tf = True
        posi = ['nan', '  ', ' ', 'nannan', '']
        if self.ill1 in ['UK', 'uk', 'Uk', 'uK']:
            self.ill1 = 'UK-UK-UK'
        if self.ill2 in posi:
            self.ill2 = today
        elif self.ill2 in ['UK', 'uk', 'Uk', 'uK']:
            self.ill2 = 'UK-UK-UK'
        if self.st in ['UK', 'uk', 'Uk', 'uK']:
            self.st = 'UK-UK-UK'
        if self.ed in posi or self.ed is None:
            self.ed = today
        elif self.ed in ['UK', 'uk', 'Uk', 'uK']:
            self.ed = 'UK-UK-UK'
        self.ill1 = self.ill1.replace('UK', '01').replace('uk', '01').replace('uK', '01').replace('Uk', '01')
        self.ill2 = self.ill2.replace('UK', '31').replace('uk', '31').replace('uK', '31').replace('Uk', '31')
        sstt = self.st.split('-') + self.ill1.split('-')
        for index in range(0, 3):
            if 'UK' in sstt[index] or 'uk' in sstt[index] or 'uK' in sstt[index] or 'Uk' in sstt[index]:
                sstt[index] = sstt[index+3]
        self.st = sstt[0] + '-' + sstt[1] + '-' + sstt[2]
        eedd = self.ed.split('-') + self.ill2.split('-')
        for index in range(0, 3):
            if 'UK' in eedd[index] or 'uk' in eedd[index] or 'uK' in eedd[index] or 'Uk' in eedd[index]:
                eedd[index] = eedd[index+3]
        self.ed = eedd[0] + '-' + eedd[1] + '-' + eedd[2]
        if self.ill1 <= self.st <= self.ill2:
            value_tf = value_tf
        else:
            value_tf = False
        return value_tf

    def value_check_only_ed(self):  # if self.ill1 <= self.ed <= self.ill2:
        value_tf = True
        posi = ['nan', '  ', ' ', 'nannan', '']
        if self.ill1 in ['UK', 'uk', 'Uk', 'uK']:
            self.ill1 = 'UK-UK-UK'
        if self.ill2 in posi:
            self.ill2 = today
        elif self.ill2 in ['UK', 'uk', 'Uk', 'uK']:
            self.ill2 = 'UK-UK-UK'
        if self.st in ['UK', 'uk', 'Uk', 'uK']:
            self.st = 'UK-UK-UK'
        if self.ed in posi or self.ed is None:
            self.ed = today
        elif self.ed in ['UK', 'uk', 'Uk', 'uK']:
            self.ed = 'UK-UK-UK'
        self.ill1 = self.ill1.replace('UK', '01').replace('uk', '01').replace('uK', '01').replace('Uk', '01')
        self.ill2 = self.ill2.replace('UK', '31').replace('uk', '31').replace('uK', '31').replace('Uk', '31')
        sstt = self.st.split('-') + self.ill1.split('-')
        for index in range(0, 3):
            if 'UK' in sstt[index] or 'uk' in sstt[index] or 'uK' in sstt[index] or 'Uk' in sstt[index]:
                sstt[index] = sstt[index+3]
        self.st = sstt[0] + '-' + sstt[1] + '-' + sstt[2]
        eedd = self.ed.split('-') + self.ill2.split('-')
        for index in range(0, 3):
            if 'UK' in eedd[index] or 'uk' in eedd[index] or 'uK' in eedd[index] or 'Uk' in eedd[index]:
                eedd[index] = eedd[index+3]
        self.ed = eedd[0] + '-' + eedd[1] + '-' + eedd[2]
        if self.ill1 <= self.ed <= self.ill2:
            value_tf = value_tf
        else:
            value_tf = False
        return value_tf


class InCheck:  # 适用于2个part_df之间的检查(提取df的names之后，for n in names而获得的part_df)
    # 如果要同时在MH2和AE里检查，可以先把MH2和AE给concat了(中间涉及rename、mh2和ae的行号备注)
    """
    def c11():
    def clean(s):
        return str(s).replace('异常有临床意义，请描述 ', '').strip(' ')

    def note_mh2(s):
        return 'MH2: ' + str(s)

    def note_ae(s):
        return 'AE: ' + str(s)
    fa2 = pd.read_excel(edc_file, sheet_name = 'FA2', usecols='l,t,ac,ad,af,ag')
    fa2 = fa2.loc[fa2['FAORRES2 '].str.contains('异常有', na=False)]
    fa2['FAORRES2 '] = fa2['FAORRES2 '].map(clean)
    names = sorted(set(fa2['USUBJID ']))

    mh2 = pd.read_excel(edc_file, sheet_name = 'MH2', usecols = 'l,t,w,aa,am,an')
    mh2 = mh2.loc[mh2['MHTERM2 '] != '  ']
    mh2.rename(columns={'MHTERM2 ': 'TERM', 'MHSTDAT2(RAW) ': 'STDAT', 'MHENDAT2(RAW) ': 'ENDAT'}, inplace=True)
    mh2['LINE '] = mh2['LINE '].map(note_mh2)

    ae = pd.read_excel(edc_file, sheet_name='AE', usecols='l,t,w,ac,ao,ap')
    ae = ae.loc[ae['AETERM '] != '  ']
    ae.rename(columns = {'AETERM ': 'TERM', 'AESTDAT(RAW) ': 'STDAT', 'AEENDAT(RAW) ': 'ENDAT'}, inplace = True)
    ae['LINE '] = ae['LINE '].map(note_ae)

    add = pd.concat([mh2, ae])

    lose = pd.DataFrame()
    time = pd.DataFrame()
    fmt = pd.DataFrame()

    for n in names:
        pfa2 = fa2.loc[fa2['USUBJID '] == n].reset_index(drop = True)
        padd = add.loc[add['USUBJID '] == n].reset_index(drop = True)

        t = InCheck(pfa2, padd).check_with_date(3, 2, 2, 3, 4, 5)

        time = pd.concat([time, t.time])
        fmt = pd.concat([fmt, t.fmt])
        lose = pd.concat([lose, t.lose])

    time['质疑'], fmt['质疑'], lose['质疑'] = '', '', ''
    xie = pd.ExcelWriter(save.format('C11'))
    time.to_excel(xie, sheet_name = '胸图能对应MH2或AE_日期逻辑问题', index = False)
    fmt.to_excel(xie, sheet_name = '胸图能对应MH2或AE_日期格式问题', index = False)
    lose.to_excel(xie, sheet_name = '胸图不能对应MH2或AE', index = False)
    xie.close()
    """
    # (受试者编号尽量不要重复，第二个编号名列要修改F)针对检查中描述存在大量分隔符，生成的额外表单，可以用来覆盖原‘腹部B超不能对应MH2或AE’，以减去不必要的核查
    """
    def c14_r_p():
    df = pd.read_excel(save.format('C14_R'), sheet_name = '右眼检查不能对应MH2或AE')
    names = sorted(set(df['USUBJID F']))
    false_dfs = pd.DataFrame()
    for n in names:
        p = df.loc[df['USUBJID F'] == n]
        desc = str(p.iloc[0, 4])
        cut = re.findall(r'\W*', desc, re.DOTALL)
        for c in range(cut.count('')):
            cut.remove('')
        for c in cut:
            desc = desc.replace(c, ',')
        check_list = desc.split(',')
        for clean in range(check_list.count('')):  # 之前遗漏，很致命
            check_list.remove('')
        for c in check_list:  # ()有时候可以忽略
            macth_cnt = 0
            time_true = 0
            for row in range(p.shape[0]):
                if c in str(p.iloc[row, 12]):
                    macth_cnt += 1
                    if DateCheck(str(p.iloc[row, 10]), str(p.iloc[row, 11]), str(p.iloc[0, 2]),
                                 str(p.iloc[0, 2])).value_check() is True:
                        time_true += 1
                    else:
                        print(n, desc, cut, check_list, str(p.iloc[row, 12]))
            if macth_cnt == 0 or time_true != 1:
                false_dfs = pd.concat([false_dfs, p])
                break
    false_dfs.to_excel(save.format('C14_R_P'), index = False)
    """
    # 加入了匹配正确的备份模块
    """
    def c60():
    def clean(s):
        return str(s).replace('既往病史，请填写名称 ', '').strip(' ')
    cm3 = pd.read_excel(edc_file, sheet_name = 'CM3', usecols = 'l,t,w,aa,ay,az,bc,be,bf')
    cm3 = cm3.loc[cm3['CMINDC3 '].str.contains('既往病史', na = False)]
    cm3['CMINDC3 '] = cm3['CMINDC3 '].map(clean)
    names = sorted(set(cm3['USUBJID ']))
    mh2 = pd.read_excel(edc_file, sheet_name = 'MH2', usecols = 'l,t,w,aa,am,an,aq')
    mh2 = mh2.loc[mh2['MHTERM2 '] != '  ']

    lose = pd.DataFrame()
    time = pd.DataFrame()
    fmt = pd.DataFrame()
    time_true = pd.DataFrame()

    for n in names:
        pc = cm3.loc[cm3['USUBJID '] == n].reset_index(drop = True)
        pm = mh2.loc[mh2['USUBJID '] == n].reset_index(drop = True)

        t = InCheck(pc, pm).check_with_date(6, 4, 5, 3, 4, 5)
        time = pd.concat([time, t.time])
        fmt = pd.concat([fmt, t.fmt])
        lose = pd.concat([lose, t.lose])
        time_true = pd.concat([time_true, t.time_true])

    time['质疑'], fmt['质疑'], lose['质疑'] = '', '', ''
    xie = pd.ExcelWriter(save.format('C60'))
    time.to_excel(xie, sheet_name = 'CM3能对应MH2_日期逻辑问题', index = False)
    fmt.to_excel(xie, sheet_name = 'CM3能对应MH2_日期格式问题', index = False)
    lose.to_excel(xie, sheet_name = 'CM3不能对应MH2', index = False)
    time_true.to_excel(xie, sheet_name = 'CM3能对应MH2_日期没问题', index = False)
    xie.close()
    """
    # 为了配合checker核查减负函数，将未对应部分的左边缺失值进行向上复制的填充，同时在格式部分添加尾列’受试者编号‘
    """
def c9():
    mh2 = pd.read_excel(file, sheet_name='MH2', usecols='c,e,j,l,n,y,z,ab')
    mh2 = mh2.loc[mh2['目前采取的措施'].str.contains('药物治疗', na=False)]
    names = sorted(set(mh2['受试者编号']))

    cm = pd.read_excel(file, sheet_name='CM', usecols='c,j,l,n,w,x,y')
    cm = cm.loc[cm['用药原因'].str.contains('病史', na=False)]

    lose = pd.DataFrame()
    time = pd.DataFrame()
    fmt = pd.DataFrame()
    time_true = pd.DataFrame()

    for n in names:
        pm = mh2.loc[mh2['受试者编号'] == n].reset_index(drop=True)
        pc = cm.loc[cm['受试者编号'] == n].reset_index(drop = True)
        pc.drop(columns=['受试者编号'], inplace=True)

        t = InCheck(pm, pc).check_with_date(4, 5, 6, 3, 4, 5, turn = True)
        time = pd.concat([time, t.time])
        fmt = pd.concat([fmt, t.fmt])
        lose = pd.concat([lose, t.lose])
        time_true = pd.concat([time_true, t.time_true])

    for row in range(1, lose.shape[0]):
        if str(lose.iloc[row, 0]) == 'nan':
            for col in range(8):
                lose.iloc[row, col] = lose.iloc[row - 1, col]
    fmt['受试者编号'] = ''
    time['质疑'], fmt['质疑'], lose['质疑'] = '', '', ''

    xie = pd.ExcelWriter(save.format('9'))
    time.to_excel(xie, sheet_name = '病史能对应用药_日期逻辑问题', index = False)
    fmt.to_excel(xie, sheet_name = '病史能对应用药_日期格式问题', index = False)
    lose.to_excel(xie, sheet_name = '病史不能对应用药', index = False)
    time_true.to_excel(xie, sheet_name = '病史能对应用药_日期没问题', index = False)
    xie.close()
    xie = pd.ExcelWriter(copy.format('9'))
    time.to_excel(xie, sheet_name = '病史能对应用药_日期逻辑问题', index = False)
    fmt.to_excel(xie, sheet_name = '病史能对应用药_日期格式问题', index = False)
    lose.to_excel(xie, sheet_name = '病史不能对应用药', index = False)
    time_true.to_excel(xie, sheet_name = '病史能对应用药_日期没问题', index = False)
    xie.close()
    """
    def __init__(self, ori_df, goal_df):
        self.ori_df = ori_df
        self.goal_df = goal_df
        self.lose = pd.DataFrame()
        self.time = pd.DataFrame()
        self.fmt = pd.DataFrame()
        self.current_ft = pd.DataFrame()
        self.time_true = pd.DataFrame()

    def check_with_date(self, ori_name: int, ori_st: int, ori_ed,
                        goal_name: int, goal_st: int, goal_ed,
                        turn=False, issame=False):  # 对应的列，描述、开始日期、结束日期
        if issame is False:
            for row_pm in range(self.ori_df.shape[0]):
                cnt = 0
                true_date = 0
                check_pm = str(self.ori_df.iloc[row_pm, ori_name]).strip(' ')  # SAS惯病，影响精确性
                for row_pc in range(self.goal_df.shape[0]):
                    check_pc = str(self.goal_df.iloc[row_pc, goal_name]).strip(' ')
                    if check_pm not in check_pc:
                        cnt += 0
                    else:
                        cnt += 1
                        mh2st = str(self.ori_df.iloc[row_pm, ori_st])
                        mh2ed = str(self.ori_df.iloc[row_pm, ori_ed])
                        cm3st = str(self.goal_df.iloc[row_pc, goal_st])
                        cm3ed = str(self.goal_df.iloc[row_pc, goal_ed])
                        if turn is False:
                            dc = DateCheck(cm3st, cm3ed, mh2st, mh2ed)
                        else:
                            dc = DateCheck(mh2st, mh2ed, cm3st, cm3ed)
                        if dc.fmt_check() is True:
                            if dc.value_check() is False:
                                step_pm = self.ori_df.iloc[[row_pm], :].reset_index(drop = True)
                                step_pc = self.goal_df.iloc[[row_pc], :].reset_index(drop = True)
                                step = pd.concat([step_pm, step_pc], axis = 1)
                                self.current_ft = pd.concat([self.current_ft, step])
                                true_date += 0
                            else:
                                step_pm = self.ori_df.iloc[[row_pm], :].reset_index(drop = True)
                                step_pc = self.goal_df.iloc[[row_pc], :].reset_index(drop = True)
                                step = pd.concat([step_pm, step_pc], axis = 1)
                                self.time_true = pd.concat([self.time_true, step])
                                true_date += 1
                        else:
                            step_pm = self.ori_df.iloc[[row_pm], :].reset_index(drop = True)
                            step_pc = self.goal_df.iloc[[row_pc], :].reset_index(drop = True)
                            step = pd.concat([step_pm, step_pc], axis = 1)
                            self.fmt = pd.concat([self.fmt, step])
                if cnt == 0:
                    step_pm = self.ori_df.iloc[[row_pm], :].reset_index(drop = True)
                    step = pd.concat([step_pm, self.goal_df], axis = 1)
                    self.lose = pd.concat([self.lose, step])
                if true_date != 0:
                    self.current_ft = pd.DataFrame()
                else:
                    self.time = pd.concat([self.time, self.current_ft])
                    self.current_ft = pd.DataFrame()
        else:
            for row_pm in range(self.ori_df.shape[0]):
                cnt = 0
                true_date = 0
                check_pm = str(self.ori_df.iloc[row_pm, ori_name]).strip(' ')  # SAS惯病，影响精确性
                for row_pc in range(self.goal_df.shape[0]):
                    check_pc = str(self.goal_df.iloc[row_pc, goal_name]).strip(' ')
                    if check_pm != check_pc:
                        cnt += 0
                    else:
                        cnt += 1
                        mh2st = str(self.ori_df.iloc[row_pm, ori_st])
                        mh2ed = str(self.ori_df.iloc[row_pm, ori_ed])
                        cm3st = str(self.goal_df.iloc[row_pc, goal_st])
                        cm3ed = str(self.goal_df.iloc[row_pc, goal_ed])
                        if turn is False:
                            dc = DateCheck(cm3st, cm3ed, mh2st, mh2ed)
                        else:
                            dc = DateCheck(mh2st, mh2ed, cm3st, cm3ed)
                        if dc.fmt_check() is True:
                            if dc.value_check() is False:
                                step_pm = self.ori_df.iloc[[row_pm], :].reset_index(drop = True)
                                step_pc = self.goal_df.iloc[[row_pc], :].reset_index(drop = True)
                                step = pd.concat([step_pm, step_pc], axis = 1)
                                self.current_ft = pd.concat([self.current_ft, step])
                                true_date += 0
                            else:
                                step_pm = self.ori_df.iloc[[row_pm], :].reset_index(drop = True)
                                step_pc = self.goal_df.iloc[[row_pc], :].reset_index(drop = True)
                                step = pd.concat([step_pm, step_pc], axis = 1)
                                self.time_true = pd.concat([self.time_true, step])
                                true_date += 1
                        else:
                            step_pm = self.ori_df.iloc[[row_pm], :].reset_index(drop = True)
                            step_pc = self.goal_df.iloc[[row_pc], :].reset_index(drop = True)
                            step = pd.concat([step_pm, step_pc], axis = 1)
                            self.fmt = pd.concat([self.fmt, step])
                if cnt == 0:
                    step_pm = self.ori_df.iloc[[row_pm], :].reset_index(drop = True)
                    step = pd.concat([step_pm, self.goal_df], axis = 1)
                    self.lose = pd.concat([self.lose, step])
                if true_date != 0:
                    self.current_ft = pd.DataFrame()
                else:
                    self.time = pd.concat([self.time, self.current_ft])
                    self.current_ft = pd.DataFrame()
        return self


class IsDupDate:  # 仅适用于日期
    # 一个日期不应同时满足>=另一个的开始，<=另一个的结束，遍历每一行
    """
    def c65():
    cm3 = pd.read_excel(edc_file, sheet_name = 'CM3', usecols = 'l,t,w,aa,ae,ay,az,bc,be,bf')
    cm3['name重复吗'] = cm3.duplicated(subset=['USUBJID ', 'CMTERM3 '], keep=False)
    cm3['code重复吗'] = cm3.duplicated(subset=['USUBJID ', 'CMTERM3 WD '], keep=False)
    o = cm3.loc[cm3['name重复吗'] == True].sort_values(by = ['USUBJID ', 'CMTERM3 ', 'AESTDAT(RAW) '])
    c = cm3.loc[cm3['code重复吗'] == True].sort_values(by = ['USUBJID ', 'CMTERM3 WD ', 'AESTDAT(RAW) '])

    wrong1 = []
    for row in range(1, o.shape[0]-1):
        last_number = o.iloc[row-1, 0]
        number = o.iloc[row, 0]
        next_number = o.iloc[row + 1, 0]

        last_name = o.iloc[row-1, 3]
        name = o.iloc[row, 3]
        next_name = o.iloc[row+1, 3]

        last_start = o.iloc[row-1, 5]
        start = o.iloc[row, 5]
        next_start = o.iloc[row+1, 5]

        last_end = o.iloc[row - 1, 6]
        end = o.iloc[row, 6]
        next_end = o.iloc[row+1, 6]
        if number == last_number and name == last_name and IsDupDate(start, last_start,
                                                                     last_end).value_check() is False:
            wrong1.append(row)
            wrong1.append(row-1)
        if number == last_number and name == last_name and IsDupDate(end, last_start,
                                                                     last_end).value_check() is False:
            wrong1.append(row)
            wrong1.append(row - 1)
        if number == next_number and name == next_name and IsDupDate(start, next_start,
                                                                     next_end).value_check() is False:
            wrong1.append(row)
            wrong1.append(row + 1)
        if number == next_number and name == next_name and IsDupDate(end, next_start,
                                                                     next_end).value_check() is False:
            wrong1.append(row)
            wrong1.append(row + 1)
    wrong1 = sorted(set(wrong1))
    o = o.iloc[wrong1, :]

    wrong2 = []
    for row in range(1, c.shape[0] - 1):
        last_number = c.iloc[row - 1, 0]
        number = c.iloc[row, 0]
        next_number = c.iloc[row + 1, 0]
        last_name = c.iloc[row - 1, 3]
        name = c.iloc[row, 3]
        next_name = c.iloc[row + 1, 3]
        last_start = c.iloc[row - 1, 5]
        start = c.iloc[row, 5]
        next_start = c.iloc[row + 1, 5]
        last_end = c.iloc[row - 1, 6]
        end = c.iloc[row, 6]
        next_end = c.iloc[row + 1, 6]
        if number == last_number and name == last_name and IsDupDate(start, last_start,
                                                                     last_end).value_check() is False:
            wrong2.append(row)
            wrong2.append(row - 1)
        elif number == last_number and name == last_name and IsDupDate(end, last_start,
                                                                       last_end).value_check() is False:
            wrong2.append(row)
            wrong2.append(row - 1)
        elif number == next_number and name == next_name and IsDupDate(start, next_start,
                                                                       next_end).value_check() is False:
            wrong2.append(row)
            wrong2.append(row + 1)
        elif number == next_number and name == next_name and IsDupDate(end, next_start,
                                                                       next_end).value_check() is False:
            wrong2.append(row)
            wrong2.append(row + 1)
    wrong2 = sorted(set(wrong2))
    c = c.iloc[wrong2, :]

    xie = pd.ExcelWriter(save.format('C65'))
    o.to_excel(xie, sheet_name = '药物名称为索引的日期重复', index = False)
    c.to_excel(xie, sheet_name = '药物编码名称为索引的日期重复', index = False)
    xie.close()
    """
    def __init__(self, to_be_checked, other_st, other_ed=None):
        self.tbc = str(to_be_checked).strip(' ')
        self.st = str(other_st).strip(' ')
        if other_ed is None:
            self.ed = None
        else:
            self.ed = str(other_ed).strip(' ')

    def fmt_check(self):
        model = re.compile(r'(\d\d\d\d|UK|uk|uK|Uk)-(\d\d|UK|uk|uK|Uk)-(\d\d|UK|uk|uK|Uk)')
        short = ['UK', 'uk', 'uK', 'Uk']
        ed_pos = ['nan', '  ', ' ', 'nannan', '', 'UK', 'uk', 'uK', 'Uk']
        format_tf = True
        if len(model.findall(self.tbc.strip(' '))) == 0 and self.tbc.strip(' ') not in ed_pos:
            format_tf = False
        else:
            format_tf = format_tf
        if len(model.findall(self.st.strip(' '))) == 0 and self.st.strip(' ') not in short:
            format_tf = False
        else:
            format_tf = format_tf
        if self.ed is None:
            format_tf = format_tf
        elif len(model.findall(self.ed.strip(' '))) == 0 and self.ed.strip(' ') not in ed_pos:
            format_tf = False
        else:
            format_tf = format_tf
        return format_tf

    def value_check(self):
        if IsDupDate(self.tbc, self.st, self.ed).fmt_check() is True:
            if self.tbc == self.st or self.tbc == self.ed:
                return False
            posi = ['nan', '  ', ' ', 'nannan', '']
            if self.tbc in posi:
                self.tbc = today
            elif self.tbc in ['UK', 'uk', 'Uk', 'uK']:
                self.tbc = 'UK-UK-UK'
            if self.st in ['UK', 'uk', 'Uk', 'uK']:
                self.st = 'UK-UK-UK'
            if self.ed in posi or self.ed is None:
                self.ed = today
            elif self.ed in ['UK', 'uk', 'Uk', 'uK']:
                self.ed = 'UK-UK-UK'

            self.tbc = self.tbc.replace('UK', '00').replace('uk', '00').replace('uK', '00').replace('Uk', '00')

            sstt = self.st.split('-') + self.tbc.split('-')
            for index in range(0, 3):
                if 'UK' in sstt[index] or 'uk' in sstt[index] or 'uK' in sstt[index] or 'Uk' in sstt[index]:
                    if sstt[index + 3][0] != '0':
                        sstt[index] = str(int(sstt[index + 3])+1)
                    else:
                        sstt[index] = '0'+str(int(sstt[index + 3]) + 1)
            self.st = sstt[0] + '-' + sstt[1] + '-' + sstt[2]

            eedd = self.ed.split('-') + self.tbc.split('-')
            for index in range(0, 3):
                if 'UK' in eedd[index] or 'uk' in eedd[index] or 'uK' in eedd[index] or 'Uk' in eedd[index]:
                    if eedd[index + 3][0] != '0':
                        eedd[index] = str(int(eedd[index + 3])+1)
                    else:
                        eedd[index] = '0'+str(int(eedd[index + 3]) + 1)
            self.ed = eedd[0] + '-' + eedd[1] + '-' + eedd[2]

            if self.st <= self.tbc <= self.ed or self.st > self.ed:
                return False
            else:
                return True
        else:
            return False


class Likelihood:  # 文本相似度比对

    def word2vec(self, word1, word2):

        if self.punctuation is False:
            pun_list = ['。', '，', '、', '？', '！', '；', '：', '“', '”', '‘', '’', '「', '」', '『', '』', '（', '）', '[', ']',
                        '〔', '〕', '【', '】', '——', '—', '……', '…', '—', '-', '～', '·', '《', '》', '〈', '〉', '﹏﹏', '___',
                        '.']
            seg_list_1 = [w for w in list(jieba.cut(word1, cut_all=False)) if w not in pun_list]
            seg_list_2 = [w for w in list(jieba.cut(word2, cut_all=False)) if w not in pun_list]
        else:
            seg_list_1 = list(jieba.cut(word1, cut_all=False))
            seg_list_2 = list(jieba.cut(word2, cut_all=False))


        total_seg_list = list(set(seg_list_1 + seg_list_2))
        seg_vec_1 = []
        seg_vec_2 = []
        for word_tol in total_seg_list:
            freq = 0
            for word in seg_list_1:
                if word_tol == word:
                    freq += 1
            seg_vec_1.append(freq)
            freq = 0
            for word in seg_list_2:
                if word_tol == word:
                    freq += 1
            seg_vec_2.append(freq)
        self.seg_vec_1, self.seg_vec_2 = seg_vec_1, seg_vec_2

    def cos_dist(self):
        if len(self.seg_vec_1) != len(self.seg_vec_2):
            return None
        part_up = 0.0
        a_sq = 0.0
        b_sq = 0.0
        for a1, b1 in zip(self.seg_vec_1, self.seg_vec_2):
            part_up += a1 * b1
            a_sq += a1 ** 2
            b_sq += b1 ** 2
        part_down = math.sqrt(a_sq * b_sq)
        if part_down == 0.0:
            return None
        else:
            return part_up / part_down

    def likelihood(self, word1, word2, punctuation=False):
        self.word1 = word1
        self.word2 = word2
        self.punctuation = punctuation
        self.word2vec(self.word1, self.word2)
        like_per = self.cos_dist()
        return like_per
