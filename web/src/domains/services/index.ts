import {
  getSessions,
  createSession,
  getSessionById,
  updateSession,
  deleteSession,
  getJobIdById,
  getJobIdsBySessionId,
  getMessagesBySessionId,
} from '@/services/chat2graph/SessionsController';

import {
  createGraphdbs,
  getGraphdbs,
  getGraphdbById,
  deleteGraphdbs,
  updateGraphdbs,
} from '@/services/chat2graph/GraphdbController';

import {
  createKnowledgebase,
  getKnowledgebases,
  deleteKnowledgebases,
  getKnowledgebasesById,
  uploadFile,
  editKnowledgebase,
  deleteFile,
  setKnowledgebasesConfig,
} from '@/services/chat2graph/KnowledgebasesController';
import { getJobResults } from '@/services/chat2graph/JobsController';

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
  // 通过 id 获取 job ids
  public getJobIdById = getJobIdById;
  // 通过 sessionid 获取 jobId
  public getJobIdsBySessionId = getJobIdsBySessionId;
  // 通过 sessionId 获取 message view
  public getMessagesBySessionId = getMessagesBySessionId;



  // job results
  public getJobResults = getJobResults;



  // 创建图数据库
  public createGraphdbs = createGraphdbs;
  // 获取所有图数据库
  public getGraphdbs = getGraphdbs;
  // 根据 id 获取图数据库详情
  public getGraphdbById = getGraphdbById;
  // 删除图数据库
  public deleteGraphdbs = deleteGraphdbs;
  // 更新图数据库
  public updateGraphdbs = updateGraphdbs;


  // 创建知识库
  public createKnowledgebase = createKnowledgebase;
  // 获取所有知识库
  public getKnowledgebases = getKnowledgebases;
  // 根据 id 获取知识库详情
  public getKnowledgebaseById = getKnowledgebasesById;
  // 删除知识库
  public deleteKnowledgebase = deleteKnowledgebases;
  // 上传文件
  public uploadFile = uploadFile;
  // 编辑知识库
  public editKnowledgebase = editKnowledgebase;
  // 删除文件
  public deleteFile = deleteFile;
  // 知识库加载
  public setKnowledgebasesConfig = setKnowledgebasesConfig;
}

export default new SessionsService();
