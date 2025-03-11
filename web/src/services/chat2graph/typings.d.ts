declare namespace API {
  interface SessionVO {
    timestamp?: string;
    id?: string;
    name?: string;
    knowledgebase_id?: string;
  }

  interface Result_Sessions_ {
    success?: boolean;
    message?: string;
    data?: Array<SessionVO>;
  }

  interface Result_Session_ {
    success?: boolean;
    message?: string;
    data?: SessionVO;
  }


  interface MessageVO {
    id?: string;
    job_id?: string | null;
    message?: string;
    message_type?: string;
    others?: null;
    role?: 'user' | 'system';
    session_id?: string;
    timestamp?: stromg;
    status?: string;
  }

  interface Result_Message_ {
    success?: boolean;
    message?: string;
    data?: MessageVO;
  }

  interface Result_Messages_ {
    success?: boolean;
    message?: string;
    data?: Array<MessageVO>;
  }

}