import { getLocale, useSearchParams } from 'umi';
import styles from './index.less'
import { Button, Tooltip } from 'antd';


const Language: React.FC = () => {
  let [searchParams, setSearchParams] = useSearchParams();
  const locale = getLocale()


  const onChangeLang = () => {

    const params = Object.fromEntries(searchParams.entries());
    const newParams = { ...params };

    if (locale === 'en-US') {
      // 如果当前是英文，删除lang参数（切换到中文）
      delete newParams.lang;
    } else {
      // 如果当前是中文，设置为英文
      newParams.lang = 'en';
    }

    setSearchParams(newParams);
  }
  return <Tooltip title='English/中文'>
    <Button
      className={styles.language}
      type='text'
      size='small'
      onClick={onChangeLang}>{locale === 'en-US' ? 'EN' : '中'}
    </Button>
  </Tooltip>
};

export default Language;
