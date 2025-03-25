import { MODAL_FORMS } from "@/constants"
import { useDatabaseEntity } from "@/domains/entities/database-manager"
import { Form, Input, message, Modal } from "antd"
import { useEffect } from "react"


interface IGraphDataModalProps {
    open: boolean
    onClose: () => void
    editId: string | null
    onFinish: () => void
    formatMessage: (key: string) => string
    is_default_db?: boolean
}
const GraphDataModal: React.FC<IGraphDataModalProps> = ({
    open,
    onClose,
    editId,
    onFinish,
    formatMessage,
    is_default_db = false
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
                    is_default_db
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

    const renderItem = (item: string, idx: number) => {
        return <Form.Item label={formatMessage(`database.modal.label${idx}`)} name={item} rules={[{ required: true, message: formatMessage(`database.modal.placeholder${idx}`) }]}>
            {
                item !== 'pwd' ? <Input maxLength={50} placeholder={formatMessage(`database.modal.placeholder${idx}`)} /> : <Input.Password maxLength={50} placeholder={formatMessage(`database.modal.placeholder${idx}`)} />
            }
        </Form.Item>
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
            {
                MODAL_FORMS?.map((key: string, idx: number) => renderItem(key, idx))
            }
        </Form>
    </Modal>
}

export default GraphDataModal
