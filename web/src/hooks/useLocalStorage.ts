
export const useLocalStorage = () => {

    const setLocalStorage = (key: string, val: any) => {
        // 存localStorage
        localStorage.setItem(key, JSON.stringify(val))
    }

    const getLocalStorage = (key: string) => {
        const val = localStorage.getItem(key)
        return val
    }

    return {
        setLocalStorage,
        getLocalStorage
    }
}