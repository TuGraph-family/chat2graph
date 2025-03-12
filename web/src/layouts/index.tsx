import { ConfigProvider } from 'antd'
import { Outlet, useLocation, setLocale } from 'umi'
import zhCN from 'antd/locale/zh_CN'
import enUS from 'antd/locale/en_US'
export default function Layout() {
    const location = useLocation();
    const searchParams = new URLSearchParams(location.search);
    const lang = searchParams.get('lang');
    const locale = lang === 'en' ? enUS : zhCN;
    setLocale(lang === 'en' ? 'en-US' : 'zh-CN');

    return <ConfigProvider locale={locale}>
        <Outlet />
    </ConfigProvider>
}