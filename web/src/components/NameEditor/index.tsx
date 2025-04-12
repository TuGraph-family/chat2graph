import { Input, Button } from 'antd';
import { CheckOutlined, CloseOutlined } from '@ant-design/icons';
import React from 'react';
import styles from './index.less';
import { useImmer } from 'use-immer';

interface Props {
  name: any;
  onConfirm: (name: React.ReactNode) => void;
  onEdited: () => void;
}

// 脚手架示例组件
const NameEditor: React.FC<Props> = (props) => {
  const { name, onConfirm, onEdited } = props;

  const [showName, setShowName] = useImmer<string>(name);



  return <Input
    onClick={(e) => { e.stopPropagation() }}
    value={showName}
    suffix={<>
      <Button
        type='text'
        size='small'
        icon={<CheckOutlined />}
        className={styles['icon-check']}
        onClick={() => {
          onConfirm?.(showName);
          onEdited?.();
        }}
      />
      <Button
        type='text'
        size='small'
        icon={<CloseOutlined />}
        className={styles['icon-cancel']}
        onClick={() => {
          onConfirm?.(name);
          onEdited?.();
        }}
      />
    </>}
    onPressEnter={(e) => {
      onConfirm?.(showName);
      onEdited?.();
    }}
    onChange={(e) => {
      setShowName(e?.target?.value);
    }}
  />;


};

export default NameEditor;
