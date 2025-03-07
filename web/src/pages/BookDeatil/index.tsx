import { Breadcrumb, Button, Popconfirm } from "antd"
import { Link, useLocation } from "umi"
import styles from './index.less'
import AsyncTable from "@/components/AsyncTable"
import BooksDrawer from "@/pages/BookDeatil/components/BooksDrawer"
import { useBooksEntity } from "@/domains/entities/books-manager"
import { useImmer } from "use-immer"
const BooksDetail = () => {
    const location = useLocation()
    console.log(location)
    const [state, setState] = useImmer<{
        open: boolean
    }>({
        open: false
    })

    const { open } = state
    const { runGetFileList, loadingGetFileList } = useBooksEntity()
    const onOpenDrawer = () => {
        setState((draft) => {
            draft.open = true
        })
    }



    const columns = [
        {
            title: '文档名',
            dataIndex: 'name',
            key: 'name',
        },
        {
            title: '文件类型',
            dataIndex: 'type',
            key: 'type',
        },
        {
            title: '数据大小',
            dataIndex: 'size',
            key: 'size',
        },
        {
            title: '状态',
            dataIndex: 'status',
            key: 'status',
        },
        {
            title: '更新时间',
            dataIndex: 'updateTime',
            key: 'updateTime',
        },
        {
            title: '操作',
            dataIndex: 'action',
            key: 'action',
            render: (text: string, record: any) => {
                return <>
                    <Button type="link" onClick={() => { }} >编辑</Button>
                    <Popconfirm
                        title={`请确定是否删除图数据库${record.name}？`}
                        onConfirm={() => { }}
                        onCancel={() => { }}
                        okText="确定"
                        cancelText="取消"
                    >
                        <Button type="link" disabled={record.isDefault}>删除</Button>
                    </Popconfirm></>
            }
        },
    ]

    return <div className={styles['books-detail']}>
        <Breadcrumb
            separator=">"
            items={[
                {
                    title: <Link to="/manager/books">知识库管理</Link>,
                },
                {
                    title: "知识库详情",
                }
            ]}
        />
        <div className={styles['books-detail-container']}>
            <div className={styles['books-detail-header']}>
                <img className={styles['books-detail-header-img']} src="https://mdn.alipayobjects.com/huamei_aw9spf/afts/img/A*GEZpQKlz_IUAAAAAAAAAAAAAeiKXAQ/original" alt="" />
                <div className={styles['books-detail-header-info']}>
                    <h2>知识库名称</h2>
                    <p>创建人：{ }</p>
                    <p>创建时间: { }</p>
                </div>
            </div>
            <div className={styles['books-detail-content']}>
                <h2>2</h2>
                <p>文档数</p>
            </div>
        </div>

        <AsyncTable
            service={runGetFileList}
            loading={loadingGetFileList}
            columns={columns}
            extra={[
                { key: 'search', searchKey: 'search', placeholder: '搜索图数据库' },
                { key: 'add', onClick: onOpenDrawer }
            ]}
        />

        <BooksDrawer open={open} onClose={() => setState((draft) => { draft.open = false })} />
    </div>
}

export default BooksDetail