import { Collapse, Skeleton } from "antd"
import styles from './index.less'
import ReactMarkdown from 'react-markdown';
import gfm from 'remark-gfm';
import { DownOutlined, UpOutlined } from "@ant-design/icons";
import ThinkStatus from "@/components/ThinkStatus";
import useIntlConfig from "@/hooks/useIntlConfig";
import { EXPERTS } from "@/constants";


const ThinkCollapse: React.FC<{ think: any }> = ({
    think,
}) => {
    const { formatMessage } = useIntlConfig();

    return <div className={styles['think-collapse']}>
        <Collapse
            collapsible="header"
            defaultActiveKey={['1']}
            expandIconPosition="end"
            expandIcon={({ isActive }) => isActive ? <UpOutlined style={{ color: '#6a6b71' }} /> : <DownOutlined style={{ color: '#6a6b71' }} />}
            items={[
                {
                    key: '1',
                    label: <p className={styles['step-thinks-title']}>
                        <ThinkStatus status={think?.status} />
                        <span className={styles['step-thinks-title-expert']}>
                            @{think?.assigned_expert_name ? formatMessage(`home.expert.${EXPERTS[think.assigned_expert_name]}`) : '导数专家'}
                        </span>
                        : {think?.goal}
                    </p>,
                    children:
                        think?.payload ? <div key={`${think?.jobId}_payload`} className={styles['step-thinks-message']}>
                            <ReactMarkdown remarkPlugins={[gfm]}>{think?.payload}</ReactMarkdown>
                        </div> : <Skeleton paragraph={{ rows: 1 }} active />
                    ,
                },
            ]}
        />
    </div>
}

export default ThinkCollapse