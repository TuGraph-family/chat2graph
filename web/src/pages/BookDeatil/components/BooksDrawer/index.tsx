import { Drawer, Steps } from "antd"

interface BooksDrawerProps {
    open: boolean
    onClose: () => void
}
const BooksDrawer: React.FC<BooksDrawerProps> = ({ open, onClose }) => {
    return <Drawer title="添加本地文件" open={open} onClose={onClose} width={700}>
        <Steps
            type="navigation"
            size="small"
            current={0}
            onChange={() => { }}
            className="site-navigation-steps"
            items={[
                {
                    title: '上传本地文件',
                    status: 'finish',
                },
                {
                    title: '数据处理配置',
                    status: 'process',
                },
            ]}
        />
    </Drawer>
}

export default BooksDrawer