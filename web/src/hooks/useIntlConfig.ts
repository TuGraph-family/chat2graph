
import { useIntl } from 'umi';

const useIntlConfig = () => {
    const intl = useIntl();

    const formatMessage = (id: string, params?: any) => {
        return intl.formatMessage({ id }, params)
    }

    return {
        formatMessage
    }
}

export default useIntlConfig
