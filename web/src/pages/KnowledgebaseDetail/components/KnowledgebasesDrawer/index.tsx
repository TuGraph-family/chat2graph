import { useKnowledgebaseEntity } from "@/domains/entities/knowledgebase-manager";
import { InboxOutlined } from "@ant-design/icons"
import { Button, Drawer, Form, Input, message, Space, Steps, Upload } from "antd"
import { UploadProps } from "antd/lib"
import { RcFile } from "antd/lib/upload";
import { useImmer } from "use-immer"
const { Dragger } = Upload;

interface KnowledgebasesDrawerProps {
    open: boolean
    onClose: (isRefresh?: boolean) => void
    formatMessage: (id: string, params?: any) => string
    id?: string,
}
const KnowledgebasesDrawer: React.FC<KnowledgebasesDrawerProps> = ({ open, onClose, formatMessage, id }) => {
    const [form] = Form.useForm()
    const [state, setState] = useImmer<{
        current: number,
        file_id: string
    }>({
        current: 0,
        file_id: "",
    })
    const { current, file_id } = state

    const { runUploadFile, runSetKnowledgebasesConfig, loadingSetKnowledgebasesConfig } = useKnowledgebaseEntity()

    const onNext = () => {
        form.validateFields(['file']).then(() => {
            setState((draft) => {
                draft.current += 1
            })
        })
    }

    const onSubmit = () => {
        form.validateFields().then(async (values) => {
            const res = await runSetKnowledgebasesConfig({
                knowledgebases_id: id,
                file_id
            }, {
                config: values?.config
            })

            if (!res?.success) {
                message.error(res?.message)
                return
            }
            setState((draft) => {
                draft.current = 0
            })
            message.success(res?.message)
            form.resetFields()
            onClose(true)


        })
    }


    const beforeUpload = async (file: RcFile) => {
        const { type, size, name } = file
        const fileBlob = new Blob([file], { type })
        if (size > 20 * 1024 * 1024) {
            message.error(formatMessage('knowledgebase.detail.upload.errorSize'))
            return false
        }
        const res = await runUploadFile({
            file: fileBlob,
            filename: name
        })
        if (!res?.success) {
            message.error(res?.message)
            return Upload.LIST_IGNORE
        }

        setState((draft) => {
            draft.file_id = res?.data?.file_id || ''
        })

        return false
    }

    const props: UploadProps = {
        name: 'file',
        accept: '.pdf,.xlsx,.txt,.doc,.docx,.md',
        maxCount: 1,
        beforeUpload,
    }

    const onCancel = () => {
        setState((draft) => {
            draft.current = 0
        })
        form.resetFields()
        onClose()
    }

    const validateJSON = (rule: any, value: string) => {
        try {
            JSON.parse(value);
            return Promise.resolve();
        } catch (e) {
            return Promise.reject(formatMessage('knowledgebase.detail.jsonTip'));
        }
    };


    return <Drawer title={formatMessage('knowledgebase.detail.addFile')} open={open} onClose={onCancel} width={700} footer={<Space>
        <Button onClick={onCancel} >{formatMessage('actions.cancel')}</Button>
        {current === 0 && <Button type="primary" onClick={onNext}>{formatMessage('actions.next')}</Button>}
        {current === 1 && <Button type="primary" onClick={onSubmit} loading={loadingSetKnowledgebasesConfig}>{formatMessage('actions.ok')}</Button>}
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

        <Form form={form} style={{ marginTop: 30 }} initialValues={{
            config: `{\n"chunk_size":512\n}`
        }}>
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
            <Form.Item name="config" rules={[{ required: true, message: formatMessage('knowledgebase.detail.configRequired') }, { validator: validateJSON }]} hidden={current !== 1}>
                <Input.TextArea rows={10} placeholder={formatMessage('knowledgebase.detail.configRequired')} />
            </Form.Item>
        </Form >
    </Drawer >
}

export default KnowledgebasesDrawer