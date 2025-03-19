import { Breadcrumb, Button, Popconfirm } from "antd"
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
    const { files, name, } = knowledgebaseEntity.knowledgebaseDetail
    const onOpenDrawer = () => {
        setState((draft) => {
            draft.open = true
        })
    }

    const onDeleteFile = (fileId: string) => {
        runDeleteFile({
            knowledgebases_id: id,
            file_id: fileId
        }).then(() => {
            getKnowledgebaseDetail(id)
        })

    }


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
        },
        {
            title: formatMessage('knowledgebase.detail.label5'),
            dataIndex: 'status',
            key: 'status',
        },
        {
            title: formatMessage('knowledgebase.detail.label6'),
            dataIndex: 'time_stamp',
            key: 'updateTime',
            render: (text: string, record: any) => {
                return <span>{dayjs(record.time_stamp).format('YYYY-MM-DD HH:mm:ss')}</span>
            }
        },
        {
            title: formatMessage('knowledgebase.detail.label7'),
            dataIndex: 'action',
            key: 'action',
            render: (text: string, record: any) => {
                return <>
                    {/* <Button type="link" onClick={() => { }} >{formatMessage('actions.edit')}</Button> */}
                    <Popconfirm
                        title={formatMessage('knowledgebase.detail.removeFile')}
                        onConfirm={() => { onDeleteFile(record.id) }}
                    >
                        <Button type="link" disabled={record.isDefault}>{formatMessage('actions.delete')}</Button>
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
        <div className={styles['knowledgebases-detail-container']}>
            <div className={styles['knowledgebases-detail-header']}>
                <img className={styles['knowledgebases-detail-header-img']} src={detailIcon} alt="" />
                <div className={styles['knowledgebases-detail-header-info']}>
                    <h2>{name}</h2>
                    {/* TODO: 暂无用户体系 */}
                    {/* <p>{formatMessage('knowledgebase.detail.label1')}：{ }</p> */}
                    <p>{formatMessage('knowledgebase.detail.label6')}：{ }</p>
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
    </div>
}

export default KnowledgebaseDetail