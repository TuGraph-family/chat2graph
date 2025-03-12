import { useDatabaseEntity } from "@/domains/entities/database-manager"
import { Form, Input, message, Modal } from "antd"
import { useEffect } from "react"


interface IGraphDataModalProps {
    open: boolean
    onClose: () => void
    editId: string | null
    onFinish: () => void
    formatMessage: (key: string) => string
}
const GraphDataModal: React.FC<IGraphDataModalProps> = ({
    open,
    onClose,
    editId,
    onFinish,
    formatMessage
}) => {
    const [form] = Form.useForm()
    const { getDatabaseDetail, databaseEntity, loadingGetGraphdbById, runCreateGraphdbs, loadingCreateGraphdbs, runUpdateGraphdbs, loadingUpdateGraphdbs } = useDatabaseEntity();



    useEffect(() => {
        if (editId) {
            getDatabaseDetail(editId)
        }
    }, [editId])


    useEffect(() => {
        if (databaseEntity?.databaseDetail) {
            form.setFieldsValue({
                ...databaseEntity?.databaseDetail
            })
        }
    }, [databaseEntity?.databaseDetail])
    const onCancel = () => {
        form.resetFields()
        onClose()
    }

    const onSubmit = () => {
        form.validateFields().then(async (values) => {
            let res: any = {}
            if (editId) {
                res = await runUpdateGraphdbs({ session_id: editId }, {
                    ...databaseEntity?.databaseDetail,
                    ...values,
                })
            } else {
                res = await runCreateGraphdbs({
                    ...values,
                    is_default_db: false
                })
            }

            if (res?.success) {
                onFinish()
                onCancel()
                message.success(res?.message)
            } else {
                message.error(res?.message)
            }
        })
    }


    return <Modal
        title={<div style={{ fontSize: 20, fontWeight: 600, textAlign: 'center' }}>
            {editId ? formatMessage('database.modal.title2') : formatMessage('database.modal.title1')}
        </div>
        }
        open={open}
        onCancel={onCancel}
        onOk={onSubmit}
        confirmLoading={loadingCreateGraphdbs || loadingUpdateGraphdbs || loadingGetGraphdbById}
    >
        <Form form={form} layout="vertical">
            <Form.Item label={formatMessage('database.modal.label1')} name="name" rules={[{ required: true, message: formatMessage('database.modal.placeholder1') }]}>
                <Input maxLength={50} placeholder={formatMessage('database.modal.placeholder1')} />
            </Form.Item>
            <Form.Item label={formatMessage('database.modal.label2')} name="ip" rules={[{ required: true, message: formatMessage('database.modal.placeholder2') }]}>
                <Input maxLength={50} placeholder={formatMessage('database.modal.placeholder2')} />
            </Form.Item>
            <Form.Item label={formatMessage('database.modal.label3')} name="port" rules={[{ required: true, message: formatMessage('database.modal.placeholder3') }]}>
                <Input maxLength={50} placeholder={formatMessage('database.modal.placeholder3')} />
            </Form.Item>
            <Form.Item label={formatMessage('database.modal.label4')} name="user" rules={[{ required: true, message: formatMessage('database.modal.placeholder4') }]}>
                <Input maxLength={50} placeholder={formatMessage('database.modal.placeholder4')} />
            </Form.Item>
            <Form.Item label={formatMessage('database.modal.label5')} name="pwd" rules={[{ required: true, message: formatMessage('database.modal.placeholder5') }]}>
                <Input.Password maxLength={50} placeholder={formatMessage('database.modal.placeholder5')} />
            </Form.Item>
            <Form.Item label={formatMessage('database.modal.label6')} name="desc" >
                <Input maxLength={50} placeholder={formatMessage('database.modal.placeholder6')} />
            </Form.Item>
        </Form>
    </Modal>
}

export default GraphDataModal
