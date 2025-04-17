
export const useLocalStorage = () => {

    const setLocalStorage = (key: string, val: any) => {
        // 存localStorage
        localStorage.setItem(key, val)
    }

    const getLocalStorage = (key: string) => {
        const val = localStorage.getItem(key)
        return val
    }

    const removeLocalStorage = (key: string) => {
        localStorage.removeItem(key)
    }

    return {
        setLocalStorage,
        getLocalStorage,
        removeLocalStorage
    }
}