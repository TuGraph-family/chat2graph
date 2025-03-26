import useIntlConfig from '@/hooks/useIntlConfig';
import { Prompts, Welcome } from '@ant-design/x';
import { Space } from 'antd';
import { GetProp } from 'antd/lib';
import React from 'react';
import logoSrc from '@/assets/logo.png';

interface Props {
  placeholderPromptsItems: GetProp<typeof Prompts, 'items'>;
  onPromptsItemClick: GetProp<typeof Prompts, 'onItemClick'>;
};

const Placeholder: React.FC<Props> = (props) => {
  const { placeholderPromptsItems, onPromptsItemClick } = props;
  const { formatMessage } = useIntlConfig();
  return <Space direction="vertical" size={16}>
    <Welcome
      variant="borderless"
      title={<img src={logoSrc} width={240} />}
      description={formatMessage('home.description')}
    />
    <Prompts
      items={placeholderPromptsItems}
      styles={{
        list: {
          width: '100%',
        },
        item: {
          flex: 1,
        },
      }}
      onItemClick={onPromptsItemClick}
    />
  </Space>
};

export default Placeholder