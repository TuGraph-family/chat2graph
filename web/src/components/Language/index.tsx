import { getLocale, useSearchParams } from 'umi';
import styles from './index.less'
import { Button, Tooltip } from 'antd';
import { ENGLISH_LANG_PARAM, ENGLISH_LOCALE } from '@/constants';


const Language: React.FC = () => {
  let [searchParams, setSearchParams] = useSearchParams();
  const locale = getLocale()


  const onChangeLang = () => {

    const params = Object.fromEntries(searchParams.entries());
    const newParams = { ...params };

    if (locale === ENGLISH_LOCALE) {
      delete newParams.lang;
    } else {
      newParams.lang = ENGLISH_LANG_PARAM;
    }

    setSearchParams(newParams);
  }
  return <Tooltip title='English/中文'>
    <Button
      className={styles.language}
      type='text'
      size='small'
      onClick={onChangeLang}>{locale === ENGLISH_LOCALE ? 'EN' : '中'}
    </Button>
  </Tooltip>
};

export default Language;
