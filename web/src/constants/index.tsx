import { Bubble } from "@ant-design/x";
import { GetProp } from "antd";
export const DEFAULT_NAME = 'Umi Max';

export enum FRAMEWORK {
  MODEL = 'MODEL',
  EXPORT_DATA = 'EXPORT_DATA',
  QUERY = 'QUERY',
};

export const ENGLISH_LOCALE = 'en-US';
export const ZH_CN_LOCALE = 'zh-CN';
export const ENGLISH_LANG_PARAM = 'en';

export const FRAMEWORK_CONFIG = [{
  key: FRAMEWORK.MODEL,
  textId: 'home.model',
  icon: 'icon-Chat2graphjianmokuangjia'
}, {
  key: FRAMEWORK.EXPORT_DATA,
  textId: 'home.exportData',
  icon: 'icon-Chat2graphbianzu'
}, {
  key: FRAMEWORK.QUERY,
  textId: 'home.query',
  icon: 'icon-Chat2graphchaxunkuangjia'
}];

export const MOCK_placeholderPromptsItems = [
  {
    key: '1',
    labelId: 'home.placeholderPromptsItems1',
  },
  {
    key: '2',
    labelId: 'home.placeholderPromptsItems2',
  },
];

export const ROLES: GetProp<typeof Bubble.List, 'roles'> = {
  ai: {
    placement: 'start',
    variant: 'borderless',
  },
  local: {
    placement: 'end',
    variant: 'borderless',
  },
};

export const MODAL_FORMS = ['name', 'type', 'host', 'port', 'user', 'pwd', 'default_schema', 'desc']

export const REQUIRED_MODAL_FORMS = ['name', 'type', 'host', 'port']

export const MESSAGE_TYPE = {
  // 任务已创建
  CREATED: 'CREATED',
  // 任务正在处理中
  RUNNING: 'RUNNING',
  // 任务已完成
  FINISHED: 'FINISHED',
  // 任务处理失败
  FAILED: 'FAILED',
  // 被终止
  STOPPED: 'STOPPED',
  // 停止
  STOP: 'STOP',
}

export const MESSAGE_TYPE_TIPS = {
  [MESSAGE_TYPE.CREATED]: 'home.status.created',
  [MESSAGE_TYPE.RUNNING]: 'home.status.running',
  [MESSAGE_TYPE.FINISHED]: 'home.status.finished',
  [MESSAGE_TYPE.FAILED]: 'home.status.failed',
  [MESSAGE_TYPE.STOPPED]: 'home.status.stopped',
}


export const CURRENT_PREFIXES = ['[当前会话]', '[Current]'];


enum EXPERT_ENUM {
  MODELLING = 'Graph Modeling Expert',
  IMPORT = 'Data Importation Expert',
  QUERY = 'Graph Query Expert',
  ANALYSIS = 'Graph Analysis Expert',
  ANSWERING = 'Question Answering Expert',
}

export const EXPERTS = {
  [EXPERT_ENUM.MODELLING]: 'MODELING',
  [EXPERT_ENUM.IMPORT]: 'IMPORT',
  [EXPERT_ENUM.QUERY]: 'QUERY',
  [EXPERT_ENUM.ANALYSIS]: 'ANALYSIS',
  [EXPERT_ENUM.ANSWERING]: 'ANSWERING',
}


export const LOCAL_STORAGE_STOP_KEY = 'MESSAGE_TOP';
export const LOCAL_STORAGE_SESSION_KEY = 'SESSION_ID_SELECTED';





