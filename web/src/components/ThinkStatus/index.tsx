import { MESSAGE_TYPE } from "@/constants";
import { Spin } from "antd";
import styles from './index.less';


const ThinkStatus = ({ status }) => {

    switch (status) {
        case MESSAGE_TYPE.CREATED:
            return <Spin percent={0} wrapperClassName={styles["created"]} />;
        case MESSAGE_TYPE.RUNNING:
            return <Spin percent={75} wrapperClassName={styles["running"]} />;
        case MESSAGE_TYPE.FINISHED:
            return <Spin percent={100} className={styles["finished"]} />;
        case MESSAGE_TYPE.FAILED:
            return <Spin percent={75} wrapperClassName={styles["failed"]} />;
        case MESSAGE_TYPE.STOPPED:
            return <Spin percent={75} wrapperClassName={styles["stopped"]} />;
        default:
            return null;
    }


}

export default ThinkStatus;