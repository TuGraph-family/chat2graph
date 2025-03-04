import { Bubble } from "@ant-design/x";
import { GetProp } from "antd";

export const DEFAULT_NAME = 'Umi Max';

export enum FRAMEWORK {
  MODEL = 'MODEL',
  EXPORT_DATA = 'EXPORT_DATA',
  QUERY = 'QUERY',
};

export const FRAMEWORK_CONFIG = [{
  key: FRAMEWORK.MODEL,
  text: '建模框架',
}, {
  key: FRAMEWORK.EXPORT_DATA,
  text: '导数框架',
}, {
  key: FRAMEWORK.QUERY,
  text: '查询框架',
}];

export const MOCK_placeholderPromptsItems = [
  {
    key: '1',
    label: '图是什么？',
  },
  {
    key: '2',
    label: '怎么用 ISOGQL 查询一个点？',
  },
];

export const ROLES: GetProp<typeof Bubble.List, 'roles'> = {
  ai: {
    placement: 'start',
    typing: true,
    messageRender: (text) => <pre>{text}</pre>,
  },
  local: {
    placement: 'end',
    variant: 'shadow',
    messageRender: (text) => <pre>{text}</pre>,
  },
};
