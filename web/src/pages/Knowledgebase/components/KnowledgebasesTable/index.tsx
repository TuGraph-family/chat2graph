import { Input, Pagination, Spin, Row, Col, Dropdown, Popconfirm, message, Modal, Form, Typography } from "antd";
import { DeleteOutlined, EditOutlined, EllipsisOutlined, SearchOutlined } from "@ant-design/icons";
import styles from './index.less'
import { debounce } from "lodash";
import { history } from "umi";
import { historyPushLinkAt } from "@/utils/link";
import { useSearchPagination } from "@/hooks/useSearchPagination";
import { useKnowledgebaseEntity } from "@/domains/entities/knowledgebase-manager";
import { useImmer } from "use-immer";

interface KnowledgebasesTableProps {
  formatMessage: (id: string, params?: any) => string
  dataSource: any[]
  loading: boolean
  onRefresh: () => void
  onDeleteKnowledgebase: (id: string) => Promise<any>
}

const KnowledgebasesTable: React.FC<KnowledgebasesTableProps> = ({
  formatMessage,
  dataSource,
  loading,
  onRefresh,
  onDeleteKnowledgebase
}) => {
  const { runEditKnowledgebase } = useKnowledgebaseEntity()
  const [state, setState] = useImmer({
    dropdownOpen: '',
    knowledgebasesId: '',
    isDeleting: false,
  })
  const { dropdownOpen, knowledgebasesId, isDeleting } = state
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




  const onEditKnowledgebase = (values: {
    name: string,
    description: string
  }, id: string) => {
    form.setFieldsValue({
      name: values?.name,
      description: values?.description
    })
    setState((draft) => {
      draft.knowledgebasesId = id
    })
  }


  const onCancel = () => {
    setState((draft) => {
      draft.knowledgebasesId = ''
    })
    form.resetFields()
  }
  const onSaveKnowledgebase = () => {
    form.validateFields().then(async (values) => {
      const res = await runEditKnowledgebase({
        knowledgebases_id: knowledgebasesId,
      }, values)
      if (res) {
        message.success(res?.message)
        onRefresh()
        onCancel()
      }
    })
  }


  const renderCard = () => {
    return <Row gutter={[16, 16]} className={styles['knowledgebases-table-card-row']}>
      {paginatedData?.map(item => {
        return <Col span={8} key={item?.id}>
          <div className={styles['knowledgebases-table-card']} onClick={() => {
            history.push(historyPushLinkAt('/manager/knowledgebase/detail', { id: item?.id, sessionId: item?.session_id }))
          }}>
            <div className={styles['knowledgebases-table-card-header']}>
              <Typography.Paragraph
                ellipsis={{
                  rows: 1,
                  tooltip: item.name
                }}
                className={styles['knowledgebases-table-card-header-title']}>
                {item?.name}
              </Typography.Paragraph>
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
                        setState((draft) => {
                          draft.dropdownOpen = ''
                        })
                      }
                    },
                    {
                      label: <Popconfirm
                        placement="right"
                        title={formatMessage('knowledgebase.home.remove')}
                        description={<div style={{ width: 200 }}>{formatMessage('knowledgebase.home.removeConfirm')}</div>}
                        onConfirm={() => {
                          onDeleteKnowledgebase(item?.id)
                          setState((draft) => {
                            draft.dropdownOpen = ''
                          })
                        }}
                        onCancel={() => setState((draft) => {
                          draft.dropdownOpen = ''
                        })}
                        onOpenChange={(open) => {
                          setState((draft) => {
                            draft.isDeleting = open
                          })
                        }}
                        icon={<DeleteOutlined />}

                      >
                        {formatMessage('knowledgebase.home.remove')}
                      </Popconfirm>,
                      icon: <DeleteOutlined />,
                      key: 'delete',
                      onClick: (e: any) => {
                        e?.domEvent.stopPropagation()
                        setState((draft) => {
                          draft.dropdownOpen = item.id
                        })
                      }
                    }
                  ]
                }}
                onOpenChange={(open, info) => {
                  if (info.source === 'trigger' && !isDeleting) {
                    setState((draft) => {
                      draft.dropdownOpen = open ? item.id : ''
                    })
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
      <div className={styles['knowledgebases-table-header-title']}>{formatMessage('knowledgebase.home.subTitle2')}</div>
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