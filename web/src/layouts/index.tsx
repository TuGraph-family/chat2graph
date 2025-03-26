import { ConfigProvider } from 'antd'
import { Outlet, useLocation, setLocale } from 'umi'
import zhCN from 'antd/locale/zh_CN'
import enUS from 'antd/locale/en_US'
import { ENGLISH_LANG_PARAM, ENGLISH_LOCALE, ZH_CN_LOCALE } from '@/constants';
export default function Layout() {
    const location = useLocation();
    const searchParams = new URLSearchParams(location.search);
    const lang = searchParams.get('lang');
    const locale = lang === ENGLISH_LANG_PARAM ? enUS : zhCN;
    setLocale(lang === ENGLISH_LANG_PARAM ? ENGLISH_LOCALE : ZH_CN_LOCALE);

    return <ConfigProvider locale={locale}>
        <Outlet />
    </ConfigProvider>
}