import { Button, Popconfirm, Tag } from 'antd'
import styles from './index.less'
import { useImmer } from 'use-immer'
import GraphDataModal from './components/GraphDataModal'
import { useDatabaseEntity } from '@/domains/entities/database-manager'

import AsyncTable from '@/components/AsyncTable'
const GraphDatabase: React.FC = () => {
    const [state, setState] = useImmer<{
        search: string
        open: boolean
        editId: number | null
        pagination: {
            current: number
            pageSize: number
        }
        dataSource: any[]
        total: number
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
    })
    const { open, editId, } = state

    const { runGetGraphDatabase, loadingGetGraphDatabase } = useDatabaseEntity()


    const onOpenModal = (id = null) => {
        setState((draft) => {
            draft.open = true
            draft.editId = id
        })
    }



    const setDefaultGraphDatabase = async (id: number) => {
        console.log(id)
    }


    const columns = [
        {
            title: '图数据库名',
            dataIndex: 'name',
            render: (text: string, record: any) => {
                return <div className={styles['graph-database-name']}>
                    {text}
                    {record.isDefault && <Tag style={{ marginLeft: 10 }} bordered={false} color="processing">
                        默认
                    </Tag>}
                </div>
            }
        },
        {
            title: 'IP地址',
            dataIndex: 'ip',
        },
        {
            title: '默认图项目',
            dataIndex: 'defaultGraphProject',
        },
        {
            title: '可用状态',
            dataIndex: 'availableStatus',
            render: (text: boolean) => {
                return text ? <Tag color="cyan" bordered={false}>可用</Tag> : <Tag color="error" bordered={false}>不可用</Tag>
            }
        },
        {
            title: '更新时间',
            dataIndex: 'updateTime',
        },
        {
            title: '操作',
            dataIndex: 'operation',
            render: (text: string, record: any) => {
                return <div className={styles['graph-database-operation']}>
                    <Button type="link" onClick={() => onOpenModal(record.id)} >编辑</Button>
                    <Popconfirm
                        title={`请确定是否删除图数据库${record.name}？`}
                        onConfirm={() => { }}
                        onCancel={() => { }}
                        okText="确定"
                        cancelText="取消"
                    >
                        <Button type="link" disabled={record.isDefault}>删除</Button>
                    </Popconfirm>
                    <Button type="link" disabled={record.isDefault} onClick={() => setDefaultGraphDatabase(record.id)}>设置为默认</Button>
                </div>
            }
        },
    ]

    return <div className={styles['graph-database']}>
        <h1>图数据库管理</h1>
        <AsyncTable
            service={runGetGraphDatabase}
            loading={loadingGetGraphDatabase}
            columns={columns}
            extra={[
                { key: 'search', searchKey: 'search', placeholder: '搜索图数据库' },
                { key: 'add', onClick: onOpenModal }
            ]}
        />

        <GraphDataModal
            editId={editId}
            open={open}
            onClose={() => setState((draft) => { draft.open = false })}
            onFinish={() => {

            }}
        />
    </div>
}

export default GraphDatabase
