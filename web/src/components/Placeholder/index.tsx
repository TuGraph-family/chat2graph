import { Prompts, Welcome } from '@ant-design/x';
import { Space } from 'antd';
import { GetProp } from 'antd/lib';
import React from 'react';

interface Props {
  placeholderPromptsItems: GetProp<typeof Prompts, 'items'>;
  onPromptsItemClick: GetProp<typeof Prompts, 'onItemClick'>;
};

const Placeholder: React.FC<Props> = (props) => {
  const { placeholderPromptsItems, onPromptsItemClick } = props;
  return <Space direction="vertical" size={16}>
    <Welcome
      variant="borderless"
      // icon="https://mdn.alipayobjects.com/huamei_iwk9zp/afts/img/A*s5sNRo5LjfQAAAAAAAAAAAAADgCCAQ/fmt.webp"
      title="TuGraph"
      description="你好，我是小图，你可以对我说"
      // extra={
      //   <Space>
      //     <Button icon={<ShareAltOutlined />} />
      //     <Button icon={<EllipsisOutlined />} />
      //   </Space>
      // }
    />
    <Prompts
      // title="Do you want?"
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