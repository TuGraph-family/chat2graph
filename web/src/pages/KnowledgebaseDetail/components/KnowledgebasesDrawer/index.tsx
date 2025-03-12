import { useKnowledgebaseEntity } from "@/domains/entities/knowledgebase-manager";
import { InboxOutlined } from "@ant-design/icons"
import { Button, Drawer, Form, Input, message, Space, Steps, Upload } from "antd"
import { UploadProps } from "antd/lib"
import { useImmer } from "use-immer"
const { Dragger } = Upload;

interface KnowledgebasesDrawerProps {
    open: boolean
    onClose: (isRefresh?: boolean) => void
    formatMessage: (id: string, params?: any) => string
}
const KnowledgebasesDrawer: React.FC<KnowledgebasesDrawerProps> = ({ open, onClose, formatMessage }) => {
    const [form] = Form.useForm()
    const [state, setState] = useImmer({
        current: 0,
    })
    const { current } = state

    const { runUploadFile } = useKnowledgebaseEntity()

    const onNext = () => {
        form.validateFields(['file']).then(() => {
            setState((draft) => {
                draft.current += 1
            })
        })
    }

    const onSubmit = () => {
        form.validateFields().then(async (values) => {
            const { originFileObj, type } = values?.file.file
            const fileBlob = new Blob([originFileObj], { type })

            const res = await runUploadFile({
                ...values,
                file: fileBlob
            })
            if (res) {
                message.success(res?.message)
                onClose(true)
            }
        })
    }

    const props: UploadProps = {
        name: 'file',
        accept: '.pdf,.txt,.doc,.docx',
        maxCount: 1,
        beforeUpload(file) {
            if (file.size > 20 * 1024 * 1024) {
                message.error(formatMessage('knowledgebase.detail.upload.errorSize'))
                return false
            }
            return true
        },
    };

    return <Drawer title={formatMessage('knowledgebase.detail.addFile')} open={open} onClose={() => onClose()} width={700} footer={<Space>
        <Button onClick={() => onClose()}>{formatMessage('actions.cancel')}</Button>
        {current === 0 && <Button type="primary" onClick={onNext}>{formatMessage('actions.next')}</Button>}
        {current === 1 && <Button type="primary" onClick={onSubmit}>{formatMessage('actions.ok')}</Button>}
    </Space>}>
        <Steps
            type="navigation"
            size="small"
            current={current}
            onChange={(current) => { setState((draft) => { draft.current = current }) }}
            className="site-navigation-steps"
            items={[
                {
                    title: formatMessage('knowledgebase.detail.step1'),
                },
                {
                    title: formatMessage('knowledgebase.detail.step2'),
                },
            ]}
        />

        <Form form={form} style={{ marginTop: 30 }}>

            <Form.Item name="file" rules={[{ required: true, message: formatMessage('knowledgebase.detail.upload.required') }]} hidden={current !== 0}>
                <Dragger {...props}>
                    <p className="ant-upload-drag-icon">
                        <InboxOutlined />
                    </p>
                    <p className="ant-upload-text">{formatMessage('knowledgebase.detail.upload.title')}</p>
                    <p className="ant-upload-hint">
                        {formatMessage('knowledgebase.detail.upload.description')}
                    </p>
                </Dragger>
            </Form.Item>
            <Form.Item name="config" rules={[{ required: true, message: formatMessage('knowledgebase.detail.configRequired') }]} hidden={current !== 1}>
                <Input.TextArea rows={10} placeholder={formatMessage('knowledgebase.detail.configRequired')} />
            </Form.Item>
        </Form >

    </Drawer >
}

export default KnowledgebasesDrawer