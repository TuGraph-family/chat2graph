import styles from './index.less';
import { Button, GetProp, Modal, Tooltip, Flex, Spin, message, Badge } from 'antd';
import { DeleteOutlined, EditOutlined, PlusOutlined, LeftCircleOutlined, RightCircleOutlined, MessageOutlined, LayoutFilled, UploadOutlined, LinkOutlined } from '@ant-design/icons';
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
import { useCallback, useEffect } from 'react';
import { useSessionEntity } from '@/domains/entities';
import useIntlConfig from '@/hooks/useIntlConfig';
import Language from '@/components/Language';
import logoSrc from '@/assets/logo.png';
import BubbleContent from '@/components/BubbleContent';
import { useLocalStorage } from '@/hooks/useLocalStorage';

const HomePage: React.FC = () => {

  const { getLocalStorage, setLocalStorage } = useLocalStorage()

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
    uplodaFileIds: { file_id: string, uid: string }[];
    closeTag: boolean;
  }>({
    conversationsItems: [],
    headerOpen: false,
    activeKey: '',
    collapse: false,
    placeholderPromptsItems: MOCK_placeholderPromptsItems,
    content: '',
    attachedFiles: [],
    isInit: false,
    uplodaFileIds: [],
    closeTag: false
  });


  const { isInit, conversationsItems, activeKey, collapse, placeholderPromptsItems, content, attachedFiles, headerOpen, uplodaFileIds, closeTag } = state;

  const { formatMessage } = useIntlConfig();

  const {
    sessionEntity,
    getSessionList,
    loadingGetSessions,
    runCreateSession,
    runUpdateSession,
    runDeleteSession,
    runGetSessionById,
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

  let timer: any = null;

  const transformMessage = (answer: any) => {
    if (!answer) return null;
    const { message, thinking, metrics } = answer || {};

    const thinkingList = thinking?.map((item: any) => {
      const { message: thinkMsg, metrics, job } = item

      return {
        payload: thinkMsg?.payload,
        message_type: thinkMsg?.message_type,
        status: metrics?.status,
        job
      }
    })
    return {
      payload: message?.payload,
      session_id: message?.session_id,
      job_id: message?.job_id,
      role: message?.role,
      thinking: thinkingList,
      status: metrics?.status
    }
  }


  const onStop = () => {
    setLocalStorage('MESSAGE_TOP', '')
  }

  const getMessage = useCallback((job_id: string, onSuccess: (message: any) => void, onUpdate: (message: any) => void) => {
    timer = setTimeout(() => {
      runGetJobResults({
        job_id,
      }).then(res => {
        const { status } = res?.data?.answer?.metrics || {};
        if (getLocalStorage("MESSAGE_TOP") === "true") {
          clearTimeout(timer);
          onSuccess({
            payload: 'STOP',
            session_id: res?.data?.answer?.message?.session_id,
            job_id,
            role: res?.data?.answer?.message?.role,
            thinking: []
          });
          onStop()
          return;
        }

        if (['RUNNING', 'CREATED'].includes(status)) {
          onUpdate(transformMessage(res?.data?.answer))
          getMessage(job_id, onSuccess, onUpdate);
          return;
        }
        clearTimeout(timer);
        onSuccess(transformMessage(res?.data?.answer));
      });
    }, 500)
  }, [closeTag])

  const getAttached = () => {
    const uid_list = attachedFiles?.map(item => item?.uid);
    const attached_list: { file_id: string, message_type: string }[] = []
    const originalAttached = attachedFiles?.map(item => {
      return {
        uid: item?.uid,
        name: item?.name,
        size: item?.size,
        percent: item?.percent
      }
    })
    uplodaFileIds?.forEach(item => {
      if (uid_list.includes(item?.uid)) {
        attached_list.push({
          file_id: item?.file_id,
          message_type: 'FILE',
        })
      }
    })

    return { attached_list, originalAttached }
  }

  const [agent] = useXAgent<API.ChatVO>({
    request: async ({ message: msg }, { onSuccess, onUpdate }) => {
      const { payload = '', session_id = '', attached_messages = {} } = msg || {};

      runGetJobIdsBySessionId({
        session_id,
      }, {
        instruction_message: {
          payload,
          message_type: 'TEXT',
        },
        attached_messages: attached_messages?.attached_list || [],
      }).then((res: API.Result_Chat_) => {
        const { job_id = '' } = res?.data || {};
        getMessage(job_id, onSuccess, onUpdate);
        onUpdate(res?.data || {})
        setState((draft) => {
          draft.uplodaFileIds = []
          draft.attachedFiles = []
          draft.headerOpen = false;
        });

      });
    },

  });
  const { onRequest, parsedMessages, setMessages } = useXChat({
    agent,
    parser: (agentMessages) => {
      return agentMessages;
    }
  });


  // 更新输入内容
  const updateContent = (newContent: string = '') => {
    setState((draft) => {
      draft.content = newContent;
    })
  }

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
          draft.uplodaFileIds = []
          draft.attachedFiles = []
          draft.headerOpen = false;
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
      }
      setMessages(res?.data?.map(item => getHistoryMessage(item))?.flat() || [])
    })

  };

  const items: GetProp<typeof Bubble.List, 'items'> = parsedMessages.map((item) => {
    // @ts-ignore
    const { message, id, status, } = item;
    return {
      key: id,
      loading: message?.role === 'SYSTEM' && !message?.thinking,
      role: message?.role === 'SYSTEM' ? 'ai' : 'local',
      content: message?.payload || formatMessage('home.noResult'),
      avatar: message?.role === 'SYSTEM' ? {
        icon: <img src={logoSrc} />
      } : undefined,
      typing: (message?.role === 'SYSTEM' && !isInit) ? { step: 3, interval: 50 } : false,
      messageRender: (text) => {
        return message?.role === 'SYSTEM' ? <BubbleContent key={id} status={message?.status} message={message} content={text} /> : <div className={styles['user-conversation']}>
          <pre className={styles['user-conversation-question']}>{text}</pre>
          {
            <Flex vertical gap="middle">
              {(message?.attached_messages?.originalAttached as any[])?.map((item) => (
                <Attachments.FileCard key={item.uid} item={item} />
              ))}
            </Flex>
          }
        </div>
      }
    }
  });


  // 新增会话
  const onAddConversation = () => {
    setMessages([]);
  };

  const onBeforeUpload = async () => {
    try {
      const { data: { id = '' } } = await runCreateSession({
        name: formatMessage('home.newConversation'),
      })
      getSessionList();
      setState((draft) => {
        draft.activeKey = id;
      });

      return id;
    } catch (error) {
      console.log('onBeforeUpload' + error)
    }

  }


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

  const onSubmit = (nextContent: string) => {
    if (!nextContent || agent.isRequesting()) return;
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
            session_id: res?.data?.id,
            attached_messages: getAttached()
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
      attached_messages: getAttached()
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

  const onAddUploadId = (fileId: { file_id: string, uid: string }) => {
    setState((draft) => {
      draft.uplodaFileIds = [...draft.uplodaFileIds, fileId]
    })
  }

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
              !collapse && <span>Chat2Graph</span>
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

        <Tooltip title={collapse ? formatMessage('home.manager') : ''}>
          <Button
            onClick={() => {
              window.open('/manager', '_blank')
            }}
            type={'text'}
            className={`${styles['go-manager']} ${collapse ? styles['go-manager-collapsed'] : ''}`}
            style={collapse ? { bottom: 52 } : {}}
            icon={<LayoutFilled />}
            size='large'
            block
            ghost={collapse ? true : false}
          >
            {collapse ? '' : formatMessage('home.manager')}
          </Button>
        </Tooltip>
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
          {/* 输入框 */}
          <Sender
            value={content}
            header={<SenderHeader
              open={headerOpen}
              onAddUploadId={onAddUploadId}
              attachedFiles={attachedFiles}
              handleFileChange={handleFileChange}
              onOpenChange={(open: boolean) => {
                setState((draft) => {
                  draft.headerOpen = open;
                });
              }}
              onBeforeUpload={onBeforeUpload}
              sessionId={activeKey} />}
            onSubmit={onSubmit}
            onChange={updateContent}
            actions={false}
            placeholder={formatMessage('home.placeholder')}
            className={styles.sender}
            onCancel={() => setLocalStorage('MESSAGE_TOP', true)}
            footer={({ components }) => {
              const { SendButton, LoadingButton } = components;
              return (
                <Flex justify="space-between" align="center">
                  <Flex gap="small" align="center">
                    {FRAMEWORK_CONFIG.map(item => <Button
                      key={item.key}
                      type={state.selectedFramework === item.key ? 'primary' : 'default'}
                      onClick={() => {
                        setState((draft) => {
                          draft.selectedFramework = draft.selectedFramework === item.key ? undefined : item.key;
                        })
                      }}
                    >
                      <i className={`iconfont  ${item.icon}`} style={{
                        fontSize: '20px', color: '#6a6b71'
                      }} />{formatMessage(item.textId)}
                    </Button>)}

                  </Flex>
                  <Flex align="center">
                    <Tooltip title={formatMessage('knowledgebase.detail.upload.description')}>
                      <Button
                        type="text"
                        icon={<i className='iconfont  icon-Chat2graphshangchuan' style={{
                          fontSize: '20px', color: '#6a6b71'
                        }} />}
                        onClick={() => {
                          setState((draft) => {
                            draft.headerOpen = !draft.headerOpen;
                          })
                        }}
                        style={{
                          fontSize: '20px'
                        }}
                      />
                    </Tooltip>



                    {agent.isRequesting() ? (
                      // <Tooltip title={'点击停止生成'}>
                      <LoadingButton type="default" />
                      // </Tooltip>
                    ) : (
                      <Tooltip title={formatMessage(`home.${content ? 'send' : 'placeholder'}`)}>
                        <SendButton type="primary" disabled={!content} />
                      </Tooltip>
                    )}
                  </Flex>
                </Flex>
              );
            }}
          />

        </footer>
      </div>
    </div >
  );
};

export default HomePage;

