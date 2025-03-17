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
    run: runGetJobIdsBySessionId,
    loading: loadingGetJobIdsBySessionId,
  } = useRequest(services.getJobIdsBySessionId, {
    manual: true,
  });




  const {
    run: runGetJobsById,
    loading: loadingGetJobsById,
  } = useRequest(services.getJobIdsById, {
    manual: true,
  });

  const {
    run: runGetJobResults,
    loading: loadingGetJobResults,
  } = useRequest(services.getJobResults, {
    manual: true,
  });

  const getSessionList = () => {
    runGetSessions({
      page: 1,
      size: 10,
    }).then(res => {
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
    runGetJobIdsBySessionId,
    loadingGetJobIdsBySessionId,
    runGetJobsById,
    loadingGetJobsById,
    runGetJobResults,
    loadingGetJobResults,
  };
};
