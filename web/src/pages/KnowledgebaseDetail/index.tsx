import { Breadcrumb, Button, Popconfirm, Spin, Tag } from "antd"
import { Link, useLocation, } from "umi"
import styles from './index.less'
import AsyncTable from "@/components/AsyncTable"
import KnowledgebasesDrawer from "@/pages/KnowledgebaseDetail/components/KnowledgebasesDrawer"
import { useKnowledgebaseEntity } from "@/domains/entities/knowledgebase-manager"
import { useImmer } from "use-immer"
import useIntlConfig from "@/hooks/useIntlConfig"
import { historyPushLinkAt } from "@/utils/link"
import { useEffect } from "react"
import dayjs from "dayjs"
import detailIcon from '@/assets/detail.svg';
import { CheckCircleOutlined, CloseCircleOutlined, SyncOutlined, } from "@ant-design/icons"
import { FileTextOutlined } from "@ant-design/icons"
const KnowledgebaseDetail = () => {
    const [state, setState] = useImmer<{
        open: boolean
    }>({
        open: false
    })
    const location = useLocation();
    const searchParams = new URLSearchParams(location.search);
    const id = searchParams.get('id') || "";

    const { open } = state
    const { getKnowledgebaseDetail, loadingGetKnowledgebaseById, knowledgebaseEntity, runDeleteFile, loadingDeleteFile } = useKnowledgebaseEntity();
    const { formatMessage } = useIntlConfig();
    const { files, name, time_stamp } = knowledgebaseEntity.knowledgebaseDetail
    const onOpenDrawer = () => {
        setState((draft) => {
            draft.open = true
        })
    }


    const onDeleteFile = (fileId: string) => {
        if (id) {
            runDeleteFile({
                knowledgebases_id: id,
                file_id: fileId
            }).then(() => {
                getKnowledgebaseDetail(id)
            })
        }

    }


    useEffect(() => {
        if (id) {
            getKnowledgebaseDetail(id)
        }
    }, [id])


    useEffect(() => {
        getKnowledgebaseDetail(id)
    }, [id])



    const columns = [
        {
            title: formatMessage('knowledgebase.detail.label2'),
            dataIndex: 'name',
            key: 'name',
        },
        {
            title: formatMessage('knowledgebase.detail.label3'),
            dataIndex: 'type',
            key: 'type',
        },
        {
            title: formatMessage('knowledgebase.detail.label4'),
            dataIndex: 'size',
            key: 'size',
            render: (size: string) => size + 'KB'
        },
        {
            title: formatMessage('knowledgebase.detail.label5'),
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => {
                switch (status) {
                    case 'success':
                        return <Tag icon={<CheckCircleOutlined />} color="success">{formatMessage('knowledgebase.detail.success')}</Tag>
                    case 'fail':
                        return <Tag icon={<CloseCircleOutlined />} color="error">{formatMessage('knowledgebase.detail.fail')}</Tag>
                    case 'pending':
                        return <Tag icon={<SyncOutlined spin />} color="processing">{formatMessage('knowledgebase.detail.pending')}</Tag>
                    default:
                        return null
                }
            }
        },
        {
            title: formatMessage('knowledgebase.detail.label6'),
            dataIndex: 'time_stamp',
            key: 'updateTime',
            render: (text: string, record: any) => {
                return <span>{dayjs(record.time_stamp * 1000).format('YYYY-MM-DD HH:mm:ss')}</span>
            }
        },
        {
            title: formatMessage('knowledgebase.detail.label7'),
            dataIndex: 'file_id',
            key: 'file_id',
            render: (file_id: string, record: any) => {
                return <>
                    {/* <Button type="link" onClick={() => { }} >{formatMessage('actions.edit')}</Button> */}
                    <Popconfirm
                        title={formatMessage('knowledgebase.detail.removeFile')}
                        onConfirm={() => { onDeleteFile(file_id) }}
                    >
                        <Button type="link">{formatMessage('actions.delete')}</Button>
                    </Popconfirm></>
            }
        },
    ]

    return <div className={styles['knowledgebases-detail']}>
        <Breadcrumb
            separator=">"
            items={[
                {
                    title: <Link to={historyPushLinkAt("/manager/knowledgebase")}>{formatMessage('knowledgebase.detail.breadcrumb1')}</Link>,
                },
                {
                    title: formatMessage('knowledgebase.detail.breadcrumb2'),
                }
            ]}
        />
        <Spin spinning={loadingGetKnowledgebaseById}>
            <div className={styles['knowledgebases-detail-container']}>
                <div className={styles['knowledgebases-detail-header']}>
                    <div className={styles['knowledgebases-detail-header-icon']}>
                        <FileTextOutlined />
                    </div>
                    <div className={styles['knowledgebases-detail-header-info']}>
                        <div className={styles['knowledgebases-detail-header-title']}>{name}</div>
                        {/* TODO: 暂无用户体系 */}
                        {/* <p className={styles['knowledgebases-detail-header-desc']}>{formatMessage('knowledgebase.detail.label1')}：{ }</p> */}
                        <p className={styles['knowledgebases-detail-header-desc']}>{formatMessage('knowledgebase.detail.label6')}：{time_stamp ? dayjs(time_stamp * 1000).format('YYYY-MM-DD HH:mm:ss') : '-'}</p>
                    </div>
                </div>
                <div className={styles['knowledgebases-detail-content']}>
                    <h2>{knowledgebaseEntity?.knowledgebaseDetail?.files?.length || 0}</h2>
                    <p>{formatMessage('knowledgebase.docs')}</p>
                </div>
            </div>

            <AsyncTable
                dataSource={files || []}
                loading={loadingGetKnowledgebaseById || loadingDeleteFile}
                columns={columns}
                extra={[
                    { key: 'search', searchKey: 'name' },
                    { key: 'add', onClick: onOpenDrawer }
                ]}
            />

            <KnowledgebasesDrawer open={open} onClose={(isRefresh) => {
                if (isRefresh && id) {
                    getKnowledgebaseDetail(id)
                }
                setState((draft) => { draft.open = false })
            }} formatMessage={formatMessage}
                id={id}
            />
        </Spin>

    </div>


}


export default KnowledgebaseDetail