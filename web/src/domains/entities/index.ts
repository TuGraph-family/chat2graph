import { useRequest } from '@umijs/max';
import { useImmer } from 'use-immer';
import services from '../services';
import { sessionListTranslator } from '../translator';
import { ConversationsProps } from '@ant-design/x';

export const useSessionEntity = () => {
  const [sessionEntity, updateSessionEntity] = useImmer<{
    sessions: ConversationsProps['items'];
  }>({
    sessions: [],
  });

  const updateSessionList = (value: ConversationsProps['items'] = []) => {
    updateSessionEntity((draft) => {
      draft.sessions = value;
    });
  };

  const {
    run: runGetSessions,
    loading: loadingGetSessions,
  } = useRequest(services.getSessions, {
    manual: true,
  });

  const {
    run: runCreateSession,
    loading: loadingCreateSession,
  } = useRequest(services.createSession, {
    manual: true,
  });

  const {
    run: runGetSessionById,
    loading: loadingGetSessionById,
  } = useRequest(services.getSessionById, {
    manual: true,
  });

  const {
    run: runDeleteSession,
    loading: loadingDeleteSession,
  } = useRequest(services.deleteSession, {
    manual: true,
  });

  const {
    run: runUpdateSession,
    loading: loadingUpdateSession,
  } = useRequest(services.updateSession, {
    manual: true,
  });

  const {
    run: runGetMessageIdByChat,
    loading: loadingGetMessageIdByChat,
  } = useRequest(services.getMessageIdByChat, {
    manual: true,
  });

  const {
    run: runGetMessagesBySessionId,
    loading: loadingGetMessagesBySessionId,
  } = useRequest(services.getMessagesBySessionId, {
    manual: true,
  });

  const {
    run: runGetMessagesById,
    loading: loadingGetMessagesById,
  } = useRequest(services.getMessageById, {
    manual: true,
  });

  const getSessionList = () => {
    runGetSessions().then(res => {
      const { data } = res || {};
      updateSessionList(sessionListTranslator(data));
    })
  };

  return {
    sessionEntity,
    getSessionList,
    loadingGetSessions,
    runCreateSession,
    loadingCreateSession,
    runGetSessionById,
    loadingGetSessionById,
    runDeleteSession,
    loadingDeleteSession,
    runUpdateSession,
    loadingUpdateSession,
    runGetMessageIdByChat,
    loadingGetMessageIdByChat,
    runGetMessagesBySessionId,
    loadingGetMessagesBySessionId,
    runGetMessagesById,
    loadingGetMessagesById,
  };
};
