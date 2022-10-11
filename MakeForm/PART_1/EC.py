def create_edit_check(names, codes, visit, page, field, notes):
    code_model = """
{}|{}|True

Check Steps:
{}

Check Actions:
OpenQuery||{}|0|{}|0|{}|0|{}|0|{}|
"""
    check_steps_code = ''
    code_list = codes.split(',')
    for code in code_list:
        if '-' in code:
            if code.count('-') == 3:
                units = code.split('-')
                datavalue_model = 'DATAVALUE|||||111|0|112|0|113|0|114|0|0||'
                idx = 111
                for unit in units:
                    if unit == '9':
                        unit = ''
                    else:
                        unit = unit
                    datavalue_model = datavalue_model.replace(str(idx), unit)
                    idx += 1
                check_steps_code += datavalue_model + '\n'
            elif code.count('-') == 4:
                units = code.split('-')
                datavalue_model = 'DATAVALUE|||||111|0|112|0|113|0|114|115|0||'
                idx = 111
                for unit in units:
                    if unit == '9':
                        unit = ''
                    else:
                        unit = unit
                    datavalue_model = datavalue_model.replace(str(idx), unit)
                    idx += 1
                check_steps_code += datavalue_model + '\n'
            else:
                pass

        elif '*n' in code:
            if '负' in code:
                code = code.replace('负', '-')
            else:
                code = code
            code = code.replace('*n', '')
            constant_model = 'CONSTANT|Numeric||长度|输入数字||0||0||0||0|0||'
            constant_model = constant_model.replace('输入数字', code)
            constant_model = constant_model.replace('长度', str(len(code)))
            check_steps_code += constant_model + '\n'
        elif '*s' in code:
            code = code.replace('*s', '')
            constant_model = 'CONSTANT|String||长度|输入数字||0||0||0||0|0||'
            constant_model = constant_model.replace('输入数字', code)
            constant_model = constant_model.replace('长度', str(len(code)))
            check_steps_code += constant_model + '\n'
        elif '*d' in code:
            if '负' in code:
                code = code.replace('负', '-')
            else:
                code = code
            code = code.replace('*d', '')
            constant_model = 'CONSTANT|Numeric||总长度.小数长度|原数值||0||0||0||0|0||'
            constant_model = constant_model.replace('原数值', code)
            constant_model = constant_model.replace('总长度', str(len(code)))
            small = code.split('.')
            small = small[-1]
            constant_model = constant_model.replace('小数长度', str(len(small)))
            check_steps_code += constant_model + '\n'
        elif '&' in code:
            if '减' in code:
                code = code.replace('减', '-')
            else:
                code = code
            code = code.replace('&', '')
            check_function_model = 'CHECK FUNCTION||动作||||0||0||0||0|0||'
            check_function_model = check_function_model.replace('动作', code)
            check_steps_code += check_function_model + '\n'
        else:
            pass
    page = page.split('(')
    page = page[0]
    field = field.split('(')
    field = field[0]
    if visit == 'nan':
        visit = ''
        moudle = ''
    else:
        visit = visit
        moudle = page
    return code_model.format(names, notes, check_steps_code, visit, moudle, page, field, notes)


#a = create_edit_check('V0-SV-SV-SVDAT,V0-DS1-DS1-DSSTDAT,&<>')
#print(a)


def code_checker():
    pass  # 如果-没在code里，说明应该带有*或&


def info_exist_date_lose(args_list):  # 最后一个参数为目标检查日期，检查结果有数据，而检查日期缺失，请补充(这种类型的质疑)
    code = ''
    idx = 0
    for arg in args_list:
        if idx == 0:
            code += arg + ',&Is Not Empty,'
        elif idx != 0 and idx != len(args_list)-1:
            code += arg + ',&Is Not Empty,&OR,'
        elif idx == len(args_list)-1:
            code += arg + ',&Is Empty,&AND'
        else:
            pass
        idx += 1
    print(code)


#info_exist_date_lose([
#'9-9-FA1-FAURES1-1', '9-9-FA1-FAURES1-2','9-9-FA1-FABRES1-1', '9-9-FA1-FABRES1-2',
#'9-9-FA1-FADAT1'            
#])
