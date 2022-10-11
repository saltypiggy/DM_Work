model = """
import com.baomidou.mybatisplus.mapper.EntityWrapper;
import com.jxedc.clinflash.customfunction.CFunction;
import com.jxedc.clinflash.customfunction.entity.CDataPoint;

import java.util.Date;
import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * 年龄：(知情同意签署日期-出生日期)/365.25，计算结果向下取整为整数（例如计算结果25.876，取整为25）。
 */
public class AGE extends CFunction {
    @Override
    public int run() {
        Long subjectId = context().getSubjectId();
        Date birthDay = null;
        List<CDataPoint> bDays = system().listDataPoints(new EntityWrapper<CDataPoint>()
                .eq("subjectId", subjectId)
                .and().eq("fieldOid", "%s")
                .and().eq("formOid","%s")
                .and().eq("folderOid", "%s"), null);
        try {
            CDataPoint dp = bDays.get(0);
            String format = dp.getDataFormat();
            birthDay = system().getDateFormat(format).parse(dp.getDataValue());
        } catch (Exception ex) {}
        Date signDate = null;
        List<CDataPoint> sDays = system().listDataPoints(new EntityWrapper<CDataPoint>()
                .eq("subjectId", subjectId)
                .and().eq("fieldOid", "%s")
                .and().eq("formOid","%s")
                .and().eq("folderOid", "%s"), null);
        try {
            CDataPoint dp = sDays.get(0);
            String format = dp.getDataFormat();
            signDate = system().getDateFormat(format).parse(dp.getDataValue());
        } catch (Exception ex) {}
        List<CDataPoint> ageDPs = system().listDataPoints(new EntityWrapper<CDataPoint>()
                .eq("subjectId", subjectId)
                .and().eq("fieldOid", "%s")
                .and().eq("formOid","%s")
                .and().eq("folderOid", "%s"), null);
        CDataPoint dp = ageDPs.get(0);
        if (birthDay == null || signDate == null) {
            system().setDataPointValue(dp.getDataPointId(), "");
        } else {
            try {
                int age = new Double((TimeUnit.DAYS.convert(signDate.getTime() - birthDay.getTime(), TimeUnit.MILLISECONDS))/ 365.25).intValue();
                system().setDataPointValue(dp.getDataPointId(), Integer.toString(age));
            } catch (Exception ex) {
                system().setDataPointValue(dp.getDataPointId(), "");
            }
        }
        return 0;
    }
}
"""


def change(bd_field='BRTHDAT', dm_form='DM', dm_folder='V0',
           knew_field='DSSTDAT1', knew_form='DS1', knew_folder='V0',
           age_field='AGE'):  # knew是’知情同意‘的意思
    return (model % (bd_field, dm_form, dm_folder,
                     knew_field, knew_form, knew_folder,
                     age_field, dm_form, dm_folder)).strip('\n')


print(change(knew_field = 'DSSTDAT'))
