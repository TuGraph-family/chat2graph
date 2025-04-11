import { MODAL_FORMS, REQUIRED_MODAL_FORMS } from "@/constants"
import { useDatabaseEntity } from "@/domains/entities/database-manager"
import { Form, Input, message, Modal, Select } from "antd"
import neo4j from "@/assets/neo4j.png"
import tugraph from "@/assets/tugraph.png"
import { useEffect } from "react"

const { Option } = Select
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
  formatMessage,
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

  const renderDom = (item: string, idx: number) => {
    switch (item) {
      case 'type':
        return <Select placeholder={formatMessage(`database.modal.placeholder${idx}`)} style={{ height: 35 }}>
          <Option value="NEO4J">
            <img src={neo4j} style={{ height: 30 }} />
          </Option>
          <Option value="TUGRAPH">
            <img src={tugraph} style={{ height: 25 }} /></Option>
        </Select>;
      case 'pwd':
        return <Input.Password maxLength={50} placeholder={formatMessage(`database.modal.placeholder${idx}`)} />;
      default:
        return <Input maxLength={50} placeholder={formatMessage(`database.modal.placeholder${idx}`)} />;
    }
  }

  const renderItem = (item: string, idx: number) => {
    return <Form.Item
      key={idx}
      label={formatMessage(`database.modal.label${idx}`)}
      name={item}
      rules={REQUIRED_MODAL_FORMS.includes(item) ? [{ required: true, message: formatMessage(`database.modal.placeholder${idx}`) }] : []}
    >
      {renderDom(item, idx)}
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
    <Form
      form={form}
      layout="vertical"
      initialValues={{
        type: 'NEO4J',
        host: 'localhost',
        port: '7687',
      }}
    >
      {
        MODAL_FORMS?.map((key: string, idx: number) => renderItem(key, idx))
      }
    </Form>
  </Modal>
}

export default GraphDataModal
