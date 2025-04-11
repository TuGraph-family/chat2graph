export const formatTimestamp = (formatMessage: (id: string, values?: any) => void, timestamp?: number) => {
    if (!timestamp) {
        return '';
    }
    const date = new Date(timestamp * 1000);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);

    const formatNumber = (n) => n < 10 ? '0' + n : n;

    if (date.toDateString() === today.toDateString()) {
        return formatMessage('home.today');
    } else if (date.toDateString() === yesterday.toDateString()) {
        return formatMessage('home.yesterday');
    } else {
        const month = formatNumber(date.getMonth() + 1);
        const day = formatNumber(date.getDate());
        return formatMessage('home.date', { month, day });
    }
}

