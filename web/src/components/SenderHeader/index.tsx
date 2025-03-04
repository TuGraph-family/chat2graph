import { CloudUploadOutlined } from '@ant-design/icons';
import { Attachments, Sender } from '@ant-design/x';
import { UploadChangeParam } from 'antd/es/upload';
import { GetProp, UploadFile } from 'antd/lib';
import React from 'react';

interface Props {
  open: boolean;
  attachedFiles?: GetProp<typeof Attachments, 'items'>;
  onOpenChange: (open: boolean) => void;
  handleFileChange: (info: UploadChangeParam<UploadFile<any>>) => void;
};

const SenderHeader: React.FC<Props> = (props) => {
  const { open, attachedFiles, onOpenChange, handleFileChange } = props;

  return <Sender.Header
    title="附件"
    open={open}
    onOpenChange={onOpenChange}
    styles={{
      content: {
        padding: 0,
      },
    }}
  >
    <Attachments
      beforeUpload={() => false}
      items={attachedFiles}
      onChange={handleFileChange}
      placeholder={(type) =>
        type === 'drop'
          ? { title: 'Drop file here' }
          : {
              icon: <CloudUploadOutlined />,
              title: '上传文件',
              description: '点击或拖拽文件到此区域',
            }
      }
    />
  </Sender.Header>
};

export default SenderHeader