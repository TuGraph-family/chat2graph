import useIntlConfig from '@/hooks/useIntlConfig';
import { Prompts, Welcome } from '@ant-design/x';
import { Space } from 'antd';
import { GetProp } from 'antd/lib';
import React from 'react';
import logoSrc from '@/assets/logo.png';
import styles from './index.less';

interface Props {
  placeholderPromptsItems: GetProp<typeof Prompts, 'items'>;
  onPromptsItemClick: GetProp<typeof Prompts, 'onItemClick'>;
};

const Placeholder: React.FC<Props> = (props) => {
  const { placeholderPromptsItems, onPromptsItemClick } = props;
  const { formatMessage } = useIntlConfig();
  return <div className={styles.placeholder}>
    <img src={logoSrc} width={40} style={{ marginRight: 8 }} />
    <Space direction="vertical" size={16} style={{ marginBottom: 120 }}>
      <Welcome
        title={formatMessage('home.title')}
        description={formatMessage('home.description')}
      />
      <Prompts
        items={placeholderPromptsItems}
        title={`💡${formatMessage('home.placeholderPromptsTitle')}：`}
        vertical

        onItemClick={onPromptsItemClick}
      />
    </Space>
  </div>

};

export default Placeholder