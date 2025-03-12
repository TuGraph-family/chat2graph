import { getLocale, useSearchParams } from 'umi';


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
    return <div style={{
        fontSize: 12,
        color: '#999',
        marginLeft: 10,
        cursor: 'pointer',
    }} onClick={onChangeLang}>
        {locale === 'en-US' ? 'EN' : '中'}
    </div>
};

export default Language;
