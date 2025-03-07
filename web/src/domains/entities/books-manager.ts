import { useRequest } from "@umijs/max"

const dataSource1 = [
    {
        id: 1,
        name: '知识库1',
        description: '知识库1描述',
        docCount: 10,
    },
    {
        id: 2,
        name: '知识库2',
        description: '知识库2描述',
        docCount: 20,
    },
    {
        id: 3,
        name: '知识库3',
        description: '知识库3描述',
        docCount: 30,
    },
    {
        id: 4,
        name: '知识库4',
        description: '知识库4描述',
        docCount: 40,
    },
    {
        id: 5,
        name: '知识库5',
        description: '知识库5描述',
        docCount: 50,
    },
    {
        id: 6,
        name: '知识库6',
        description: '知识库6描述',
        docCount: 60,
    },

]


const dataSource2 = [
    {
        id: 1,
        name: '文档名',
        type: '文件类型',
        size: 100,
        status: '添加中',
        updateTime: '2021-01-01 12:00:00',
    },
    {
        id: 2,
        name: '文档名',
        type: '文件类型',
        size: 100,
        status: '添加中',
        updateTime: '2021-01-01 12:00:00',
    },
    {
        id: 3,
        name: '文档名',
        type: '文件类型',
        size: 100,
        status: '添加中',
    },
    {
        id: 4,
        name: '文档名',
        type: '文件类型',
        size: 100,
        status: '添加中',
    },
    {
        id: 5,
        name: '文档名',
        type: '文件类型',
        size: 100,
        status: '添加中',
    },
    {
        id: 6,
        name: '文档名',
        type: '文件类型',
        size: 100,
        status: '添加中',
    },
    {
        id: 7,
        name: '文档名',
        type: '文件类型',
        size: 100,
        status: '添加中',
    },

    {
        id: 8,
        name: '文档名',
        type: '文件类型',
        size: 100,
        status: '添加中',
    },
    {
        id: 9,
        name: '文档名',
        type: '文件类型',
        size: 100,
        status: '添加中',
    },
    {
        id: 10,
        name: '文档名',
        type: '文件类型',
        size: 100,
        status: '添加中',
    },

]
export const useBooksEntity = () => {



    const testGraphDatabase = (params: any) => {
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    current: params.current,
                    pageSize: params.pageSize,
                    data: dataSource1,
                    total: 100,
                })
            }, 1000)
        })
    }

    const testFileList = (params: any) => {
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    current: params.current,
                    pageSize: params.pageSize,
                    data: dataSource2,
                    total: 100,
                })
            }, 1000)
        })
    }





    const {
        run: runGetBooks,
        loading: loadingGetBooks,
    } = useRequest(testGraphDatabase, {
        manual: true,
    });


    const {
        run: runGetFileList,
        loading: loadingGetFileList,
    } = useRequest(testFileList, {
        manual: true,
    });

    return {
        runGetBooks,
        loadingGetBooks,
        runGetFileList,
        loadingGetFileList,
    }
}