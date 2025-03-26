import { useState, useMemo } from 'react';

interface UseSearchPaginationProps<T> {
    data: T[];
    searchKey: keyof T;
    defaultPageSize?: number;
}

export function useSearchPagination<T>({
    data,
    searchKey,
    defaultPageSize = 6
}: UseSearchPaginationProps<T>) {
    const [searchText, setSearchText] = useState('');
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(defaultPageSize);

    const filteredData = useMemo(() => {
        setCurrentPage(1)
        const filtered = searchText
            ? data.filter(item =>
                String(item[searchKey]).toLowerCase().includes(searchText.toLowerCase())
            )
            : data;

        return filtered;
    }, [data, searchText, searchKey]);

    const paginatedData = useMemo(() => {
        const startIndex = (currentPage - 1) * pageSize;
        return filteredData.slice(startIndex, startIndex + pageSize);
    }, [filteredData, currentPage, pageSize]);

    const total = filteredData.length;

    return {
        paginatedData,
        total,
        currentPage,
        pageSize,
        searchText,
        setSearchText,
        setCurrentPage,
        setPageSize
    };
} 