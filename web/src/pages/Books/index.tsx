import { EllipsisOutlined } from "@ant-design/icons"
import { Dropdown } from "antd"
import styles from './index.less'
import BooksTable from "./components/BooksTable"
const Books = () => {

    const items = [
        {
            label: '删除',
            key: 'delete',
        },
    ]
    return <div>
        <h1>知识库</h1>
        <div className={styles['knowledge-base-total']}>
            <div className={styles['knowledge-base-total-header']}>
                <div>
                    <h2>知识库列表</h2>
                </div>
                <Dropdown menu={{ items }}>
                    <EllipsisOutlined style={{ fontSize: 20 }} />
                </Dropdown>
            </div>
            <div className={styles['knowledge-base-total-content']}>
                <div className={styles['knowledge-base-total-content-name']}>
                    XXXX知识库
                </div>
                <div className={styles['knowledge-base-total-content-info']}>
                    <h2>10</h2>
                    <div className={styles['knowledge-base-total-content-info-desc']}>文档数</div>
                </div>
            </div>
        </div>
        <BooksTable />
    </div>
}

export default Books