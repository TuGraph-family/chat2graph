import { Input, Button } from 'antd';
import { CheckOutlined, CloseOutlined } from '@ant-design/icons';
import React from 'react';
import styles from './index.less';
import { useImmer } from 'use-immer';

interface Props {
  name: React.ReactNode;
  editing: boolean;
  onConfirm: (name: React.ReactNode) => void;
}

// 脚手架示例组件
const NameEditor: React.FC<Props> = (props) => {
  const { name, editing, onConfirm } = props;
  const [showName, setShowName] = useImmer<React.ReactNode>(name);

  if (!editing) {
    return showName;
  }

  return <Input
    suffix={<>
      <Button
        type='text'
        size='small'
        icon={<CheckOutlined />}
        className={styles['icon-check']}
        onClick={() => {
          onConfirm?.(showName);
        }}
      />
      <Button
        type='text'
        size='small'
        icon={<CloseOutlined />}
        className={styles['icon-cancel']}
        onClick={() => {
          onConfirm?.(name);
        }}
      />
    </>}
    onPressEnter={(e) => {
      onConfirm?.(showName);
    }}
    onChange={(e) => {
      setShowName(e?.target?.value);
    }}
  />;
};

export default NameEditor;
