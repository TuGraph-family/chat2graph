import { Breadcrumb, Spin, } from "antd"
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
import { FileTextOutlined } from "@ant-design/icons"
import { useKnowledgeColumns } from "@/hooks/useKnowledgeColumns"
const KnowledgebaseDetail = () => {
    const [state, setState] = useImmer<{
        open: boolean
    }>({
        open: false
    })
    const location = useLocation();
    const searchParams = new URLSearchParams(location.search);
    const id = searchParams.get('id') || "";
    const sessionId = searchParams.get('sessionId') || "";
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

    const { columns } = useKnowledgeColumns({
        onDeleteFile
    })



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
                        <div className={styles['knowledgebases-detail-header-title']}>{sessionId ? name : formatMessage('knowledgebase.home.subTitle1')}</div>
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

            <KnowledgebasesDrawer
                open={open}
                onClose={(isRefresh) => {
                    if (isRefresh && id) {
                        getKnowledgebaseDetail(id)
                    }
                    setState((draft) => { draft.open = false })
                }}
                formatMessage={formatMessage}
                id={id}

            />
        </Spin>
    </div>
}

export default KnowledgebaseDetail