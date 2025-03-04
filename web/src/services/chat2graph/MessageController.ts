import { request } from '@umijs/max';

/**
 * 通过 session_id 获取所有的 message
*/
export async function getMessagesBySessionId(
  body?: {
    session_id?: string;
  },
  options?: { [key: string]: any },
) {
  return request<API.Result_Messages_>('/api/messages/filter', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
    ...(options || {}),
  });
}

/**
 * 通过 sessionid 获取 messageid
*/
export async function getMessageIdByChat(
  body?: {
    session_id: string;
    message: string;
  },
  options?: { [key: string]: any },
) {
  return request<API.Result_Message_>(`/api/messages/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
    ...(options || {}),
  });
}

/**
 * 通过 ID 获取 message
*/
export async function getMessageById(
  params: {
    message_id?: string;
  },
  options?: { [key: string]: any },
) {
  return request<API.Result_Message_>(`/api/messages/${params.message_id}`, {
    method: 'GET',
    ...(options || {}),
  },);
}
