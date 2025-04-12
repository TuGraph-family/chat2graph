import { MESSAGE_TYPE } from "@/constants";
import { Spin } from "antd";
import styles from './index.less';



interface IThinkStatusProps {
    status?: string;
    percent?: number
}


const ThinkStatus: React.FC<IThinkStatusProps> = ({ status, percent = 0 }) => {

    switch (status) {
        case MESSAGE_TYPE.CREATED:
            return <Spin percent={1} className={styles["created"]} />;
        case MESSAGE_TYPE.RUNNING:
            return <Spin percent={percent || 75} className={styles["running"]} />;
        case MESSAGE_TYPE.FINISHED:
            return <Spin percent={100} className={styles["finished"]} />;
        case MESSAGE_TYPE.FAILED:
            return <Spin percent={75} className={styles["failed"]} />;
        case MESSAGE_TYPE.STOPPED:
            return <Spin percent={75} className={styles["stopped"]} />;
        default:
            return null;
    }


}

export default ThinkStatus;