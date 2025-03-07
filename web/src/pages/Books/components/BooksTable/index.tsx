import { Input, Pagination, Spin, Row, Col, Dropdown, Popconfirm } from "antd";
import { DeleteOutlined, EditOutlined, EllipsisOutlined, SearchOutlined } from "@ant-design/icons";
import { useImmer } from "use-immer";
import styles from './index.less'
import { useBooksEntity } from "@/domains/entities/books-manager";
import { useEffect } from "react";
import { debounce } from "lodash";
import { history } from "umi";
const BooksTable = () => {
    const [state, setState] = useImmer<{
        pagination: {
            page: number,
            pageSize: number,
            total: number,
        },
        search: string,
        dataSource: any[],
    }>({
        pagination: {
            page: 1,
            pageSize: 6,
            total: 0,
        },
        search: '',
        dataSource: [],
    })

    const { dataSource, pagination, search } = state
    const { runGetBooks, loadingGetBooks } = useBooksEntity()


    const getBooks = async () => {
        const res = await runGetBooks({
            page: pagination.page,
            pageSize: pagination.pageSize,
            search,
        })
        setState((draft) => {
            draft.dataSource = res.data
            draft.pagination.total = res.total
        })
    }

    const handleSearch = debounce((value: string) => {
        setState((draft) => {
            draft.search = value
        })
    }, 500)

    useEffect(() => {
        getBooks()
    }, [pagination.page, pagination.pageSize, search])

    const items = [
        {
            label: '编辑',
            icon: <EditOutlined />,
            key: 'edit',
            onClick: () => {
                console.log('编辑')
            }
        },
        {
            label: <Popconfirm
                title="清空知识库"
                description="将会清空知识库的全部内容，影响对应会话的输出，请确定是否清空？"
                onConfirm={() => { }}
                onCancel={() => { }}
                icon={<DeleteOutlined />}
                okText="确定"
                cancelText="取消"
            >
                清空知识库
            </Popconfirm>,
            icon: <DeleteOutlined />,
            key: 'delete',
            onClick: (e: any) => {
                e?.domEvent.stopPropagation()
                console.log(e)
            }
        }
    ]

    const renderCard = () => {
        return <Row gutter={[16, 16]} className={styles['books-table-card-row']}>
            {dataSource?.map(item => {
                return <Col span={8} key={item?.id}>
                    <div className={styles['books-table-card']} onClick={() => {
                        history.push(`/manager/books/detail?id=${item?.id}`)
                    }}>
                        <div className={styles['books-table-card-header']}>
                            <h2>{item?.name}</h2>
                            <Dropdown menu={{ items }}>
                                <EllipsisOutlined style={{ fontSize: 25, fontWeight: 600 }} />
                            </Dropdown>
                        </div>
                        <div className={styles['books-table-card-content']}>
                            <h2>{item?.docCount}</h2>
                            <p>文档数</p>
                        </div>
                    </div>
                </Col>
            })}
        </Row>
    }


    return <div className={styles['books-table']}>
        <div className={styles['books-table-header']}>
            <h2>知识库名称</h2>
            <Input className={styles['books-table-header-input']} placeholder="请输入知识库名称" prefix={<SearchOutlined />} onChange={(e) => handleSearch(e.target.value)} />
        </div>
        <Spin spinning={loadingGetBooks} >
            {renderCard()}
        </Spin>
        <Pagination
            align="end"
            current={pagination.page}
            pageSize={6}
            showSizeChanger={false}
            total={pagination.total}
            onChange={(page) => {
                setState((draft) => {
                    draft.pagination.page = page
                })
            }}
        />
    </div>
}

export default BooksTable;