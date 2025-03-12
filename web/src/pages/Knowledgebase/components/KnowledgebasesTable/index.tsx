import { Input, Pagination, Spin, Row, Col, Dropdown, Popconfirm, message, Modal, Form } from "antd";
import { DeleteOutlined, EditOutlined, EllipsisOutlined, SearchOutlined } from "@ant-design/icons";
import styles from './index.less'
import { debounce } from "lodash";
import { history } from "umi";
import { historyPushLinkAt } from "@/utils/link";
import { useSearchPagination } from "@/hooks/useSearchPagination";
import { useKnowledgebaseEntity } from "@/domains/entities/knowledgebase-manager";
import { useState } from "react";

interface KnowledgebasesTableProps {
    formatMessage: (id: string, params?: any) => string
    dataSource: any[]
    loading: boolean
    onRefresh: () => void
}

const KnowledgebasesTable: React.FC<KnowledgebasesTableProps> = ({
    formatMessage,
    dataSource,
    loading,
    onRefresh
}) => {
    const { runDeleteKnowledgebase, runEditKnowledgebase } = useKnowledgebaseEntity()
    const [knowledgebasesId, setKnowledgebasesId] = useState('')
    const [dropdownOpen, setDropdownOpen] = useState<string>('')
    const [form] = Form.useForm()
    const {
        paginatedData,
        total,
        currentPage,
        setSearchText,
        setCurrentPage
    } = useSearchPagination({
        data: dataSource,
        searchKey: "name",
        defaultPageSize: 6
    });

    const handleSearch = debounce((value: string) => {
        setSearchText(value)
    }, 500)


    const onDeleteKnowledgebase = async (id: string) => {
        const res = await runDeleteKnowledgebase({
            knowledgebases_id: id
        })
        if (res) {
            message.success(res?.message)
            onRefresh()
        }
    }

    const onEditKnowledgebase = (values: {
        name: string,
        description: string
    }, id: string) => {
        form.setFieldsValue({
            name: values?.name,
            description: values?.description
        })
        setKnowledgebasesId(id)
    }


    const onCancel = () => {
        setKnowledgebasesId('')
        form.resetFields()
    }
    const onSaveKnowledgebase = () => {
        form.validateFields().then(async (values) => {
            const res = await runEditKnowledgebase({
                knowledgebases_id: knowledgebasesId,
            }, values)
            if (res) {
                message.success(res?.message)
                onCancel()
            }
        })
    }


    const renderCard = () => {
        return <Row gutter={[16, 16]} className={styles['knowledgebases-table-card-row']}>
            {paginatedData?.map(item => {
                return <Col span={8} key={item?.id}>
                    <div className={styles['knowledgebases-table-card']} onClick={() => {
                        history.push(historyPushLinkAt('/manager/knowledgebase/detail', { id: item?.id }))
                    }}>
                        <div className={styles['knowledgebases-table-card-header']}>
                            <h2>{item?.name}</h2>
                            <Dropdown
                                trigger={['hover']}
                                open={dropdownOpen === item.id}
                                menu={{
                                    items: [
                                        {
                                            label: formatMessage('actions.edit'),
                                            icon: <EditOutlined />,
                                            key: 'edit',
                                            onClick: (e: any) => {
                                                e?.domEvent.stopPropagation()
                                                onEditKnowledgebase({
                                                    name: item?.name,
                                                    description: item?.description
                                                }, item?.id)
                                                setDropdownOpen('')
                                            }
                                        },
                                        {
                                            label: <Popconfirm
                                                placement="right"
                                                title={formatMessage('knowledgebase.home.remove')}
                                                description={formatMessage('knowledgebase.home.removeConfirm')}
                                                onConfirm={() => {
                                                    onDeleteKnowledgebase(item?.id)
                                                    setDropdownOpen('')
                                                }}
                                                onCancel={() => setDropdownOpen('')}
                                                icon={<DeleteOutlined />}
                                            >
                                                {formatMessage('knowledgebase.home.remove')}
                                            </Popconfirm>,
                                            icon: <DeleteOutlined />,
                                            key: 'delete',
                                            onClick: (e: any) => {
                                                e?.domEvent.stopPropagation()
                                                setDropdownOpen(item.id)
                                            }
                                        }
                                    ]
                                }}
                                onOpenChange={(open, info) => {
                                    if (info.source === 'trigger') {
                                        setDropdownOpen(open ? item.id : '')
                                    }
                                }}
                            >
                                <EllipsisOutlined style={{ fontSize: 25, fontWeight: 600 }} onClick={(e) => e.stopPropagation()} />
                            </Dropdown>
                        </div>
                        <div className={styles['knowledgebases-table-card-content']}>
                            <h2>{item?.file_count || 0}</h2>
                            <p>{formatMessage('knowledgebase.docs')}</p>
                        </div>
                    </div>
                </Col>
            })}
        </Row>
    }



    return <div className={styles['knowledgebases-table']}>
        <div className={styles['knowledgebases-table-header']}>
            <h2>{formatMessage('knowledgebase.home.subTitle2')}</h2>
            <Input className={styles['knowledgebases-table-header-input']} placeholder="Search" prefix={<SearchOutlined />} onChange={(e) => handleSearch(e.target.value)} />
        </div>
        <Spin spinning={loading} >
            {renderCard()}
        </Spin>
        <Pagination
            align="end"
            current={currentPage}
            pageSize={6}
            showSizeChanger={false}
            total={total}
            onChange={(page) => {
                setCurrentPage(page)
            }}
        />

        <Modal
            open={!!knowledgebasesId}
            onCancel={onCancel}
            onOk={onSaveKnowledgebase}
            title={formatMessage('knowledgebase.home.edit')}
        >
            <Form
                form={form}
                layout="vertical"
            >
                <Form.Item
                    label={formatMessage('knowledgebase.home.name')}
                    name="name"
                    rules={[{ required: true, message: formatMessage('knowledgebase.home.nameRequired') }]}
                >
                    <Input />
                </Form.Item>
                <Form.Item
                    label={formatMessage('knowledgebase.home.description')}
                    name="description"
                >
                    <Input.TextArea />
                </Form.Item>
            </Form>
        </Modal>
    </div>
}

export default KnowledgebasesTable;