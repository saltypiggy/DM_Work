def hide(sheet, show_list, hide_list, show_num=1, hide_num=2):
    def get_show():
        show_res = []
        for name in show_list:
            show_res.append('fieldList.add("%s");' % name)
        return '\n            '.join(show_res)

    def get_hide():
        hide_res = []
        for name in hide_list:
            hide_res.append('fieldList2.add("%s");' % name)
        return '\n            '.join(hide_res)
    model = """
import com.jxedc.clinflash.customfunction.CFunction;
import com.jxedc.clinflash.customfunction.entity.CFunctionParam;
import com.jxedc.clinflash.customfunction.entity.FunctionResult;
    
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
    
public class %s extends CFunction {
    public int run() {
        Long dataPageId = context().getDataPageId();
        List<String> fieldList = new ArrayList<>();
        List<String> fieldList2 = new ArrayList<>();
        List<CFunctionParam> params = context().getFunctionParams();
        String selfValue = "";
        String selfOID = "";
        for(CFunctionParam param : params) {
            if(param.getSelf() == 1) {
                selfValue = param.getDataValue();
                selfOID = param.getFieldOid();
            }
        }
        if(selfValue.equals("%s")) {
            %s
    } else if(selfValue.equals("%s")) {
            %s
        } else {
            %s
        }
        context().result().setResult(FunctionResult.SHOW_FIELD, fieldList);
        context().result().setResult(FunctionResult.HIDE_FIELD, fieldList2);
        return 0;
    }
}
""" % (sheet, show_num, get_show(), hide_num, get_hide(), get_hide())
    return model.strip('\n')


res = hide('IOP2_Eye_02', ['IOPTIM3', 'IOPRES3'],
                           ['IOPTIM3', 'IOPRES3'],
           show_num = 1, hide_num = 2)
print(res)
