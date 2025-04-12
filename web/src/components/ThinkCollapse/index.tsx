import { Collapse, Skeleton, Spin } from "antd"
import styles from './index.less'
import ReactMarkdown from 'react-markdown';
import gfm from 'remark-gfm';
import { DownOutlined, UpOutlined } from "@ant-design/icons";
import ThinkStatus from "@/components/ThinkStatus";


const ThinkCollapse: React.FC<{ think: any }> = ({
    think,
}) => {
    return <div className={styles['think-collapse']}>
        <Collapse
            collapsible="header"
            defaultActiveKey={['1']}
            expandIconPosition="end"
            expandIcon={({ isActive }) => isActive ? <UpOutlined style={{ color: '#6a6b71' }} /> : <DownOutlined style={{ color: '#6a6b71' }} />}
            items={[
                {
                    key: '1',
                    label: <div className={styles['step-thinks-title']}>
                        <ThinkStatus status={think?.status} />
                        <div className={styles['step-thinks-title-expert']}>
                            {think?.assigned_expert_name ? think?.assigned_expert_name : '@数据导入专家'}
                        </div>
                        <div className={styles['step-thinks-title-goal']}> : {think?.goal}</div>
                    </div>,
                    children:
                        think?.payload ? <div key={`${think?.jobId}_payload`} className={styles['step-thinks-message']}>
                            {/* <pre>{think?.payload}</pre> */}
                            <ReactMarkdown remarkPlugins={[gfm]}>{think?.payload}</ReactMarkdown>
                        </div> : <Skeleton paragraph={{ rows: 1 }} active />
                    ,
                },
            ]}
        />
    </div>
}

export default ThinkCollapse