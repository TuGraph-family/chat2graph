import { Form, Input, Modal } from "antd"
import { useEffect } from "react"


interface IGraphDataModalProps {
    open: boolean
    onClose: () => void
    editId: number | null
    onFinish: () => void
}
const GraphDataModal: React.FC<IGraphDataModalProps> = ({
    open,
    onClose,
    editId,
    onFinish
}) => {
    const [form] = Form.useForm()

    useEffect(() => {
        if (editId) {
            form.setFieldsValue({

            })
        }
    }, [editId])
    const onCancel = () => {
        form.resetFields()
        onClose()
    }

    const onSubmit = () => {
        form.validateFields().then((values) => {
            console.log(values)
            onFinish()
            onCancel()
        })
    }




    return <Modal
        title={<div style={{ fontSize: 20, fontWeight: 600, textAlign: 'center' }}>
            {editId ? "编辑图数据库" : "添加图数据库"}
        </div>
        }
        open={open}
        onCancel={onCancel}
        onOk={onSubmit}
    >
        <Form form={form} layout="vertical">
            <Form.Item label="图数据库名称" name="name" rules={[{ required: true, message: '请输入图数据库名称' }]}>
                <Input maxLength={50} placeholder="请输入图数据库名称" />
            </Form.Item>
            <Form.Item label="IP地址" name="ip" rules={[{ required: true, message: '请输入IP地址' }]}>
                <Input maxLength={50} placeholder="请输入IP地址" />
            </Form.Item>
            <Form.Item label="Port" name="port" rules={[{ required: true, message: '请输入Port' }]}>
                <Input maxLength={50} placeholder="请输入Port" />
            </Form.Item>
            <Form.Item label="用户名" name="username" rules={[{ required: true, message: '请输入用户名' }]}>
                <Input maxLength={50} placeholder="请输入用户名" />
            </Form.Item>
            <Form.Item label="密码" name="password" rules={[{ required: true, message: '请输入密码' }]}>
                <Input.Password maxLength={50} placeholder="请输入密码" />
            </Form.Item>
            <Form.Item label="默认图项目" name="defaultGraphProject" >
                <Input maxLength={50} placeholder="请输入默认图项目" />
            </Form.Item>
        </Form>
    </Modal>
}

export default GraphDataModal
