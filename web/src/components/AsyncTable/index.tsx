import { Button, Input, Space, Table, TableProps } from 'antd'
import styles from './index.less'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons'
import { useImmer } from 'use-immer'
import { debounce } from 'lodash'
import { useEffect } from 'react'



interface AsyncTableProps extends TableProps<any> {
    service: (params: any) => Promise<any>,
    loading: boolean,
    columns: any[],
    extra: any[],
}

const AsyncTable: React.FC<AsyncTableProps> = ({
    service,
    loading,
    columns,
    extra,
    ...otherProps
}) => {
    const [state, setState] = useImmer<{
        search: string
        open: boolean
        editId: number | null
        pagination: {
            current: number
            pageSize: number
        }
        dataSource: any[]
        total: number,
        searchKey: string | null
    }>({
        search: '',
        open: false,
        editId: null,
        pagination: {
            current: 1,
            pageSize: 10,
        },
        dataSource: [],
        total: 0,
        searchKey: null
    })
    const { search, pagination, dataSource, total, searchKey } = state;
    const getGraphDatabase = async (params: any) => {
        const res = await service(params)
        setState((draft) => {
            draft.dataSource = res.data
            draft.total = res.total
        })
    }


    useEffect(() => {

        const params: any = {
            current: pagination.current,
            pageSize: pagination.pageSize,
        }

        if (searchKey) {
            params[searchKey] = search
        }


        getGraphDatabase(params)
    }, [pagination.current, pagination.pageSize, search])


    const onSearch = debounce((value: string, key = null) => {
        setState((draft) => {
            draft.search = value
            draft.searchKey = key
        })
    }, 500)

    const renderExtra = () => {
        if (!extra) {
            return null
        }
        return <div className={styles['async-table-extra']}>
            <Space>
                {
                    extra?.map((item: any) => {
                        switch (item.key) {
                            case 'search': return <Input placeholder={item.placeholder} prefix={<SearchOutlined />} onChange={(e) => {
                                onSearch(e.target.value, item.searchKey)
                            }} />
                            case 'add': return <Button type="primary" onClick={item.onClick}><PlusOutlined />新增</Button>
                        }
                        return item
                    })
                }
            </Space>
        </div>
    }

    return <div>
        {renderExtra()}
        <div className={styles['async-table-table']}>
            <Table
                loading={loading}
                columns={columns}
                dataSource={dataSource}
                onChange={(pagination) => {
                    setState((draft) => {
                        draft.pagination = {
                            current: pagination.current || 1,
                            pageSize: pagination.pageSize || 10,
                        }
                    })
                }}
                pagination={{
                    total: total,
                    current: pagination.current,
                    pageSize: pagination.pageSize,
                }}
                {...otherProps}
            />
        </div>
    </div>
}

export default AsyncTable