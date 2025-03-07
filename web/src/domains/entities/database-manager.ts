import { useRequest } from "@umijs/max"

const dataSource = [
    {
        id: 1,
        name: '图数据库1',
        ip: '192.168.1.1',
        isDefault: true,
        defaultGraphProject: '默认图项目1',
        availableStatus: true,
        updateTime: '2021-01-01 12:00:00',
        operation: '操作',
    },
    {
        id: 2,
        name: '图数据库2',
        ip: '192.168.1.2',
        defaultGraphProject: '默认图项目2',
        availableStatus: true,
        updateTime: '2021-01-02 12:00:00',
        operation: '操作',
    },
    {
        id: 3,
        name: '图数据库3',
        ip: '192.168.1.3',
        defaultGraphProject: '默认图项目3',
        availableStatus: false,
        updateTime: '2021-01-03 12:00:00',
        operation: '操作',
    },
    {
        id: 4,
        name: '图数据库4',
        ip: '192.168.1.4',
        defaultGraphProject: '默认图项目4',
        availableStatus: true,
        updateTime: '2021-01-04 12:00:00',
        operation: '操作',
    },
    {
        id: 5,
        name: '图数据库5',
        ip: '192.168.1.5',
        defaultGraphProject: '默认图项目5',
        availableStatus: false,
        updateTime: '2021-01-05 12:00:00',
        operation: '操作',
    },
    {
        id: 6,
        name: '图数据库6',
        ip: '192.168.1.6',
        defaultGraphProject: '默认图项目6',
        availableStatus: true,
        updateTime: '2021-01-06 12:00:00',
        operation: '操作',
    },
    {
        id: 7,
        name: '图数据库7',
        ip: '192.168.1.7',
        defaultGraphProject: '默认图项目7',
        availableStatus: true,
        updateTime: '2021-01-07 12:00:00',
        operation: '操作',
    },
    {
        id: 8,
        name: '图数据库8',
        ip: '192.168.1.8',
        defaultGraphProject: '默认图项目8',
        availableStatus: false,
        updateTime: '2021-01-08 12:00:00',
        operation: '操作',
    },
    {
        id: 9,
        name: '图数据库9',
        ip: '192.168.1.9',
        defaultGraphProject: '默认图项目9',
        availableStatus: true,
        updateTime: '2021-01-09 12:00:00',
        operation: '操作',
    },
    {
        id: 10,
        name: '图数据库10',
        ip: '192.168.1.10',
        defaultGraphProject: '默认图项目10',
        availableStatus: true,
        updateTime: '2021-01-10 12:00:00',
        operation: '操作',
    },
]
export const useDatabaseEntity = () => {



    const testGraphDatabase = (params: any) => {
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    current: params.current,
                    pageSize: params.pageSize,
                    data: dataSource,
                    total: 100,
                })
            }, 1000)
        })
    }

    const {
        run: runGetGraphDatabase,
        loading: loadingGetGraphDatabase,
    } = useRequest(testGraphDatabase, {
        manual: true,
    });

    return {
        runGetGraphDatabase,
        loadingGetGraphDatabase
    }
}