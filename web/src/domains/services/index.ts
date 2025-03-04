import {
  getSessions,
  createSession,
  getSessionById,
  updateSession,
  deleteSession,
} from '@/services/chat2graph/SessionsContraoller';

import {
  getMessageIdByChat,
  getMessagesBySessionId,
  getMessageById,
} from '@/services/chat2graph/MessageController';

class SessionsService {
  // 请求会话列表
  public getSessions = getSessions;
  // 创建会话
  public createSession = createSession;
  // 根据会话 id 获取会话详情
  public getSessionById = getSessionById;
  // 更新会话（重命名）
  public updateSession = updateSession;
  // 删除会话
  public deleteSession = deleteSession;

  // 聊天过程根据输入返回输出
  public getMessageIdByChat = getMessageIdByChat;
  // 根据 sessionid 获取聊天所有上下文
  public getMessagesBySessionId = getMessagesBySessionId;
  // 根据 messageid 获取查询结果
  public getMessageById = getMessageById;
}

export default new SessionsService();
