import styles from './index.less';
import { Badge, Button, GetProp, Modal, Tooltip, Flex, Spin, message } from 'antd';
import { DeleteOutlined, EditOutlined, PlusOutlined, LeftCircleOutlined, RightCircleOutlined, UploadOutlined, MessageOutlined, UserOutlined } from '@ant-design/icons';
import {
  Attachments,
  Bubble,
  Conversations,
  ConversationsProps,
  Prompts,
  Sender,
  useXAgent,
  useXChat,
} from '@ant-design/x';
import { useImmer } from 'use-immer';
import NameEditor from '@/components/NameEditor';
import { FRAMEWORK, FRAMEWORK_CONFIG, MOCK_placeholderPromptsItems, ROLES } from '@/constants';
import Placeholder from '@/components/Placeholder';
import SenderHeader from '@/components/SenderHeader';
import { useEffect } from 'react';
import { useSessionEntity } from '@/domains/entities';

const HomePage: React.FC = () => {
  
  const [state, setState] = useImmer<{
    selectedFramework?: FRAMEWORK;
    conversationsItems: ConversationsProps['items'];
    headerOpen: boolean;
    activeKey: string;
    collapse: boolean;
    placeholderPromptsItems: GetProp<typeof Prompts, 'items'>;
    content: string;
    attachedFiles: GetProp<typeof Attachments, 'items'>;
  }>({
    conversationsItems: [],
    headerOpen: false,
    activeKey: '',
    collapse: false,
    placeholderPromptsItems: MOCK_placeholderPromptsItems,
    content: '',
    attachedFiles: [],
  });


  const { conversationsItems, activeKey, collapse, placeholderPromptsItems, content, attachedFiles, headerOpen } = state;

  const {
    sessionEntity,
    getSessionList,
    loadingGetSessions,
    runCreateSession,
    runUpdateSession,
    runDeleteSession,
    runGetSessionById,
    runGetMessageIdByChat,
    runGetMessagesBySessionId,
    runGetMessagesById,
    loadingGetMessagesById,
  } = useSessionEntity();
  const { sessions } = sessionEntity;

  const onConversationRename = (name: React.ReactNode, key: string) => {
    runUpdateSession({
      session_id: key,
    }, {
      name: name as string,
    }).then((res: API.Result_Session_) => {
      const { success } = res;
      if (success) {
        getSessionList();
      }
    });
  };

  const menuConfig: ConversationsProps['menu'] = (conversation) => ({
    items: [
      {
        label: '重命名',
        key: 'rename',
        icon: <EditOutlined />,
      },
      {
        label: '删除',
        key: 'delete',
        icon: <DeleteOutlined />,
        danger: true,
      },
    ],
    onClick: (menuInfo) => {
      const {key: menuKey} = menuInfo || {};
      if (menuKey === 'delete') {
        Modal.warning({
          title: '删除对话',
          content: '删除后无法恢复，是否继续删除？',
          okText: '确认',
          cancelText: '取消',
          onOk: () => {
            runDeleteSession({
              session_id: conversation.key,
            }).then((res: API.Result_Session_) => {
              if (res?.success) {
                getSessionList();
                message.success('删除成功');
              }
            })
          }
        });
        return;
      }

      setState((draft) => {
        draft.conversationsItems = (draft.conversationsItems || []).map(item => {
          if (item.key !== conversation.key) {
            return item;
          }
    
          return {
            ...item,
            label: <NameEditor
              name={item.label}
              editing={true}
              onConfirm={(name: React.ReactNode) => {
                onConversationRename(name, conversation.key);
              }}
            />,
          };
        });
      });
    },
  });

  const onAddConversation = () => {
    setMessages([]);
  };

  const onConversationClick: GetProp<typeof Conversations, 'onActiveChange'> = (key: string) => {
    runGetSessionById({
      session_id: key,
    }).then((res: API.Result_Session_) => {
      if (res.success) {
        setState((draft) => {
          draft.activeKey = key;
        });
      }
    });

    runGetMessagesBySessionId({
      session_id: key,
    }).then((res: any) => {
      setMessages(res?.data || []);
    })

  };

  let timer: any = null;
  const getMessage = (message_id: string, onSuccess: (message: API.MessageVO) => void) => {
    timer = setTimeout(() => {
      runGetMessagesById({
        message_id,
      }).then(res => {
        const { status } = res?.data || {};

        if (status === 'running') {
          getMessage(message_id, onSuccess);
          return;
        }

        clearTimeout(timer);
        onSuccess(res?.data || {});
      });
    }, 500);
  }

  const [agent] = useXAgent<API.MessageVO>({
    request: async ({ message: msg }, { onSuccess, onUpdate }) => {
      const { message = '', session_id = '' } = msg || {}; 
      runGetMessageIdByChat({
        message,
        session_id,
      }).then((res: API.Result_Message_) => {
        const { id: message_id = '' } = res?.data || {};
        getMessage(message_id, onSuccess);
        onUpdate(res?.data || {})
      });
    },
  });

  const { onRequest, parsedMessages, setMessages } = useXChat({
    agent,
    parser: (agentMessages) => {
      return agentMessages;
    },
  });

  const items: GetProp<typeof Bubble.List, 'items'> = parsedMessages.map((item) => {
    // @ts-ignore
    const { id, message, role, status } = item;
    return {
      key: id,
      loading: status === 'loading',
      role: message?.role === 'system' ? 'ai' : 'local',
      content: message?.message || '暂未搜索到',
      avatar: message?.role === 'system' ? {
        icon: 'GU'
      } : undefined,
  }
});

  const onSubmit = (nextContent: string) => {
    if (!nextContent) return; 

    // 新建对话
    if (!items.length) {
      runCreateSession({
        name: nextContent,
      }).then((res: API.Result_Session_) => {
        if (res.success) {
          getSessionList();
          setState((draft) => {
            draft.activeKey = res?.data?.id || '';
          });
          onRequest({
            message: nextContent,
            session_id: res?.data?.id
          });
          updateContent('');
        }
      });
      return;
    }

    // 已有对话更新
    onRequest({
      message: nextContent,
      session_id: state.activeKey,
    });
    updateContent('');
  };

  // 点击推荐项
  const onPromptsItemClick: GetProp<typeof Prompts, 'onItemClick'> = (info) => {
    onSubmit(info.data.label as string)
  };

  const handleFileChange: GetProp<typeof Attachments, 'onChange'> = (info) => {
    setState((draft) => {
      draft.attachedFiles = info.fileList;
    })
  }

  // 更新输入内容
  const updateContent = (newContent: string = '') => {
    setState((draft) => {
      draft.content = newContent;
    })
  }

  useEffect(() => {
    setState((draft) => {
      draft.conversationsItems = sessions?.map(item => {
        return {
          ...item,
          icon: <MessageOutlined />,
        }
      })
    })
  }, [sessions]);

  // 初始化请求对话列表
  useEffect(() => {
    getSessionList();
  }, []);

  return (
    <div className={styles.wrapper}>
      <div className={`${styles.sider} ${collapse ? styles['sider-collapsed'] : ''}`}>
        <div className={styles.title}>
          <span className={styles['title-text']}>TuGraph</span>
          <Tooltip
            title={collapse ? '打开边栏' : '收起边栏'}
          >
            <Button
              type='text'
              icon={collapse ? <RightCircleOutlined /> : <LeftCircleOutlined />}
              className={styles['sider-collapsed-icon']}
              onClick={() => {
                setState((draft) => {
                  draft.collapse = !draft.collapse;
                })
              }}
            />
          </Tooltip>
        </div>

        <Tooltip title={collapse ? '开启新对话' : ''}>
          <Button
            onClick={onAddConversation}
            type={collapse ? 'text' : 'primary'}
            className={styles['create-conversation']}
            icon={<PlusOutlined />}
            block
            ghost={collapse ? false : true}
          >
            {collapse ? '' : '新对话'}
          </Button>
        </Tooltip>

        <Spin spinning={loadingGetSessions} >
          <Conversations
            items={conversationsItems}
            className={styles.conversations}
            activeKey={activeKey}
            onActiveChange={onConversationClick}
            menu={menuConfig}
          />
        </Spin>
        <p className={styles.tips}>仅展示最近 10 条对话</p>
      </div>

      <div className={styles.chat}>
        {/* 消息列表 */}
        <Bubble.List
          items={items.length > 0 ? items : [{
            content: <Placeholder 
              placeholderPromptsItems={placeholderPromptsItems}
              onPromptsItemClick={onPromptsItemClick}
            />,
            variant: 'borderless',
          }]}
          roles={ROLES}
          className={`${styles.messages} ${!items.length ? styles.welcome : ''}`}
        />

        <footer className={styles.footer}>
          {/* 框架 */}
          <Flex wrap gap={12}>
            {FRAMEWORK_CONFIG.map(item => <Button
              key={item.key}
              type={state.selectedFramework === item.key ? 'primary' : 'default'}
              onClick={() => {
                setState((draft) => {
                  draft.selectedFramework = draft.selectedFramework === item.key ? undefined : item.key;
                })
              }}
            >
              {item.text}
            </Button>)}
          </Flex>

          {/* 输入框 */}
          <Sender
            value={content}
            header={<SenderHeader
              open={headerOpen}
              attachedFiles={attachedFiles}
              handleFileChange={handleFileChange}
              onOpenChange={(open: boolean) => {
              setState((draft) => {
                draft.headerOpen = open;
              });
            }}/>}
            onSubmit={onSubmit}
            onChange={updateContent}
            // 上传文件先关闭入口
            // prefix={<Badge dot={attachedFiles.length > 0 && !headerOpen}>
            //   <Button
            //     type="text"
            //     icon={<UploadOutlined />}
            //     onClick={() => {
            //       setState((draft) => {
            //         draft.headerOpen = !draft.headerOpen;
            //       })
            //     }}
            //     style={{
            //       fontSize: '20px'
            //     }}
            //   />
            // </Badge>
            // }
            loading={agent.isRequesting()}
            className={styles.sender}
          />
        </footer>
      </div>
    </div>
  );
};

export default HomePage;
