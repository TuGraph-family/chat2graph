import styles from './index.less';
import { Button, GetProp, Modal, Tooltip, Flex, Spin, message, FloatButton } from 'antd';
import { DeleteOutlined, EditOutlined, PlusOutlined, LeftCircleOutlined, RightCircleOutlined, MessageOutlined, LayoutFilled } from '@ant-design/icons';
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
import useIntlConfig from '@/hooks/useIntlConfig';
import Language from '@/components/Language';
import logoSrc from '@/assets/logo.png';
import BubbleContent from '@/components/BubbleContent';

const HomePage: React.FC = () => {

  const [state, setState] = useImmer<{
    selectedFramework?: FRAMEWORK;
    conversationsItems: ConversationsProps['items'];
    headerOpen: boolean;
    activeKey: string;
    collapse: boolean;
    placeholderPromptsItems: { labelId: string, key: string }[];
    content: string;
    attachedFiles: GetProp<typeof Attachments, 'items'>;
    isInit: boolean;
  }>({
    conversationsItems: [],
    headerOpen: false,
    activeKey: '',
    collapse: false,
    placeholderPromptsItems: MOCK_placeholderPromptsItems,
    content: '',
    attachedFiles: [],
    isInit: false
  });


  const { isInit, conversationsItems, activeKey, collapse, placeholderPromptsItems, content, attachedFiles, headerOpen } = state;

  const { formatMessage } = useIntlConfig();

  const {
    sessionEntity,
    getSessionList,
    loadingGetSessions,
    runCreateSession,
    runUpdateSession,
    runDeleteSession,
    runGetSessionById,
    runGetJobById,
    runGetJobResults,
    runGetJobIdsBySessionId,
    runGetMessagesBySessionId,
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
        label: formatMessage('home.rename'),
        key: 'rename',
        icon: <EditOutlined />,
      },
      {
        label: formatMessage('home.delete'),
        key: 'delete',
        icon: <DeleteOutlined />,
        danger: true,
      },
    ],
    onClick: (menuInfo) => {
      const { key: menuKey } = menuInfo || {};
      if (menuKey === 'delete') {
        Modal.warning({
          title: formatMessage('home.deleteConversation'),
          content: formatMessage('home.deleteConversationConfirm'),
          okText: formatMessage('home.confirm'),
          cancelText: formatMessage('home.cancel'),
          onOk: () => {
            runDeleteSession({
              session_id: conversation.key,
            }).then((res: API.Result_Session_) => {
              if (res?.success) {
                getSessionList();
                message.success(formatMessage('home.deleteConversationSuccess'));
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

  let timer: any = null;


  const transformMessage = (answer: any) => {
    if (!answer) return null;
    const { message, thinking } = answer || {};

    const thinkingList = thinking?.map((item: any) => {
      const { message: thinkMsg, metrics } = item

      return {
        payload: thinkMsg?.payload,
        message_type: thinkMsg?.message_type,
        status: metrics?.status,
      }
    })
    return {
      payload: message?.payload,
      session_id: message?.session_id,
      job_id: message?.job_id,
      role: message?.role,
      thinking: thinkingList,
    }
  }


  const getMessage = (job_id: string, onSuccess: (message: any) => void) => {
    timer = setTimeout(() => {
      runGetJobResults({
        job_id,
      }).then(res => {
        const { status } = res?.data?.answer?.metrics || {};

        if (['RUNNING', 'CREATED'].includes(status)) {
          getMessage(job_id, onSuccess);
          return;
        }
        clearTimeout(timer);
        onSuccess(transformMessage(res?.data?.answer));
      });
    }, 500);
  }

  const [agent] = useXAgent<API.ChatVO>({
    request: async ({ message: msg }, { onSuccess, onUpdate }) => {
      const { payload = '', session_id = '' } = msg || {};
      runGetJobIdsBySessionId({
        session_id,
      }, {
        instruction_message: {
          payload,
          message_type: 'TEXT',
        }, attached_messages: []
      }).then((res: API.Result_Chat_) => {
        const { job_id = '' } = res?.data || {};
        getMessage(job_id, onSuccess);
        onUpdate(res?.data || {})
      });
    },
  });
  const { onRequest, parsedMessages, setMessages } = useXChat({
    agent,
    parser: (agentMessages) => {
      return agentMessages;
    }
  });

  const onAddConversation = () => {
    setMessages([]);
  };


  const getHistoryMessage = (data: API.JobVO) => {

    const { answer, question } = data || {};
    const viewItem = [
      {
        id: question?.message?.id,
        message: question?.message,
        status: 'success',
      },
      {
        id: answer?.message?.id,
        message: transformMessage(answer),
        status: 'success',
      }
    ]

    return viewItem
  }

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
    }).then((res: API.Result_Messages_) => {

      if (res?.data?.length) {
        setState((draft) => {
          draft.isInit = true;
        });
        setMessages(res?.data?.map(item => getHistoryMessage(item))?.flat() || [])
      }

    })

  };

  const items: GetProp<typeof Bubble.List, 'items'> = parsedMessages.map((item) => {
    // @ts-ignore
    const { message, id, status, } = item;
    return {
      key: id,
      loading: status === 'loading',
      role: message?.role === 'SYSTEM' ? 'ai' : 'local',
      content: message?.payload || formatMessage('home.noResult'),
      avatar: message?.role === 'SYSTEM' ? {
        icon: <img src={logoSrc} />
      } : undefined,
      typing: (message?.role === 'SYSTEM' && !isInit) ? { step: 3, interval: 50 } : false,
      messageRender: (text) => {
        return message?.role === 'SYSTEM' ? <BubbleContent status={status} message={message} content={text} /> : <pre>{text}</pre>
      }
    }
  });



  // 更新输入内容
  const updateContent = (newContent: string = '') => {
    setState((draft) => {
      draft.content = newContent;
    })
  }

  const onSubmit = (nextContent: string) => {
    if (!nextContent) return;
    setState((draft) => {
      draft.isInit = false;
    });

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
            payload: nextContent,
            session_id: res?.data?.id
          });
          updateContent('');
        }
      });
      return;
    }

    // 已有对话更新
    onRequest({
      payload: nextContent,
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

  const onTranslate = (items: { labelId: string, key: string }[]): GetProp<typeof Prompts, 'items'> => {
    return items.map(item => {
      return {
        ...item,
        label: formatMessage(item.labelId),
      }
    })
  }
  return (
    <div className={styles.wrapper}>
      <div className={`${styles.sider} ${collapse ? styles['sider-collapsed'] : ''}`}>
        <div className={styles.title}>
          <span className={styles['title-text']}>
            <img src={logoSrc} className={styles['title-logo']} />
            {
              !collapse && <span>TuGraph</span>
            }
          </span>
          {
            !collapse && <div className={styles['title-right']}>
              <Language />
              <Tooltip title={formatMessage('home.expand')}>
                <Button
                  type='text'
                  icon={<LeftCircleOutlined />}
                  className={styles['sider-collapsed-icon']}
                  onClick={() => {
                    setState((draft) => {
                      draft.collapse = !draft.collapse;
                    })
                  }}
                />
              </Tooltip>
            </div>
          }
        </div>

        <Tooltip title={collapse ? formatMessage('home.openNewConversation') : ''}>
          <Button
            onClick={onAddConversation}
            type={collapse ? 'text' : 'primary'}
            className={styles['create-conversation']}
            icon={<PlusOutlined />}
            size='large'
            block
            ghost={collapse ? true : false}
          >
            {collapse ? '' : formatMessage('home.newConversation')}
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
        <p className={styles.tips}>{formatMessage('home.tips')}</p>
        {
          collapse ? <Tooltip
            title={formatMessage('home.collapse')}
          >
            <Button
              type='text'
              icon={<RightCircleOutlined />}
              className={styles['sider-collapsed-icon']}
              onClick={() => {
                setState((draft) => {
                  draft.collapse = !draft.collapse;
                })
              }}
            />
          </Tooltip> : null
        }
      </div>

      <div className={
        [styles.chat,
        !items?.length ? styles['chat-emty'] : ''].join(' ')}>
        {/* 消息列表 */}
        <Bubble.List
          items={items.length > 0 ? items : [{
            content: <Placeholder
              placeholderPromptsItems={onTranslate(placeholderPromptsItems)}
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
              {formatMessage(item.textId)}
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
              }} />}
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
          <FloatButton
            tooltip={<div>{formatMessage('home.manager')}</div>}
            shape="circle"
            type="primary"
            icon={<LayoutFilled />}
            onClick={() => {
              window.open('/manager', '_blank')
            }}
          />
        </footer>
      </div>
    </div>
  );
};

export default HomePage;
