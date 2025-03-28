import useIntlConfig from "@/hooks/useIntlConfig";
import { formatBytes } from "@/utils/formatBytes";
import { CheckCircleOutlined, CloseCircleOutlined, SyncOutlined } from "@ant-design/icons";
import { Button, Popconfirm, Tag } from "antd"
import dayjs from "dayjs";



export const useKnowledgeColumns = ({
    onDeleteFile
}: {
    onDeleteFile: (file_id: string) => void;
}) => {
    const { formatMessage } = useIntlConfig();
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
            render: (type: string) => {
                switch (type) {
                    case 'LOCAL':
                        return formatMessage('knowledgebase.detail.local')
                    default:
                        return null
                }
            }
        },
        {
            title: formatMessage('knowledgebase.detail.label4'),
            dataIndex: 'size',
            key: 'size',
            render: (size: string) => formatBytes(size)
        },
        {
            title: formatMessage('knowledgebase.detail.label5'),
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => {
                switch (status) {
                    case 'SUCCESS':
                        return <Tag icon={<CheckCircleOutlined />} color="success">{formatMessage('knowledgebase.detail.success')}</Tag>
                    case 'FAIL':
                        return <Tag icon={<CloseCircleOutlined />} color="error">{formatMessage('knowledgebase.detail.fail')}</Tag>
                    case 'PENDING':
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
            render: (file_id: string,) => {
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

    return { columns }
}