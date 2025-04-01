import { useKnowledgebaseEntity } from '@/domains/entities/knowledgebase-manager';
import useIntlConfig from '@/hooks/useIntlConfig';
import { CloudUploadOutlined } from '@ant-design/icons';
import { Attachments, Sender } from '@ant-design/x';
import { RcFile, UploadChangeParam } from 'antd/es/upload';
import { GetProp, message, UploadFile, UploadProps } from 'antd/lib';
import React from 'react';

interface Props {
  open: boolean;
  attachedFiles?: GetProp<typeof Attachments, 'items'>;
  onOpenChange: (open: boolean) => void;
  handleFileChange: (info: UploadChangeParam<UploadFile<any>>) => void;
  onAddUploadId: (fileId: { file_id: string, uid: string }) => void
  sessionId?: string;
};

const SenderHeader: React.FC<Props> = (props) => {
  const { open, attachedFiles, onOpenChange, handleFileChange, onAddUploadId, sessionId } = props;
  const { runUploadFile } = useKnowledgebaseEntity()
  const { formatMessage } = useIntlConfig();



  const beforeUpload = async (file: RcFile) => {
    const { type, size, name } = file
    const fileBlob = new Blob([file], { type })
    if (size > 20 * 1024 * 1024) {
      message.error(formatMessage('knowledgebase.detail.upload.errorSize'))
      return false
    }
    const res = await runUploadFile({
      session_id: sessionId,
    }, {
      file: fileBlob,
      filename: name
    })

    onAddUploadId({
      file_id: res?.data?.file_id || '',
      uid: file.uid
    })

    return res?.data?.file_id
  }




  return <Sender.Header
    title={formatMessage('home.attachment')}
    open={open}
    onOpenChange={onOpenChange}
    styles={{
      content: {
        padding: 0,
      },
    }}
  >
    <Attachments
      beforeUpload={beforeUpload}
      name='file'
      accept='.pdf,.txt,.doc,.docx,.md'
      items={attachedFiles}
      onChange={handleFileChange}
      placeholder={(type) =>
        type === 'drop'
          ? { title: 'Drop file here' }
          : {
            icon: <CloudUploadOutlined />,
            title: formatMessage('knowledgebase.detail.upload.title'),
            description: formatMessage('knowledgebase.detail.upload.description'),
          }
      }
    />
  </Sender.Header>
};

export default SenderHeader