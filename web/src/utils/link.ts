


export const historyPushLinkAt = (path: string, params?: Record<string, any>) => {
    const { search } = window.location;
    let newPath = path
    let newSearch = params ? new URLSearchParams(params).toString() : ''

    //  把search 转成对象
    const searchParams = new URLSearchParams(search);
    const lang = searchParams.get('lang');
    if (lang) {
        newSearch = newSearch ? `${newSearch}&lang=${lang}` : `lang=${lang}`
    }
    if (newSearch) {
        return `${newPath}?${newSearch}`
    }
    return newPath
};