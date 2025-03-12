declare namespace API {
  interface SessionVO {
    created_at?: string;
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

  interface FileVO {
    name?: string;
    size?: number;
    type?: string;
    status?: string;
    time_stamp?: number;
    file_id?: string;
  }


  interface KnowledgebaseVO {
    id?: string;
    name?: string;
    knowledge_type?: "graph" | "vector";
    session_id?: string;
    file_count?: number;
    files?: Array<FileVO>;
  }

  interface GraphdbVO {
    desc?: string;
    id?: string;
    ip?: string;
    is_default_db?: boolean;
    name?: string;
    port?: string;
    pwd?: string;
    user?: string;
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

  interface Result_Knowledgebases_ {
    success?: boolean;
    message?: string;
    data?: Array<KnowledgebaseVO>;
  }

  interface Result_Knowledgebase_ {
    success?: boolean;
    message?: string;
    data?: KnowledgebaseVO;
  }



  interface Result_Graphdbs_ {
    success?: boolean;
    message?: string;
    data?: Array<GraphdbVO>;
  }

  interface Result_Graphdb_ {
    success?: boolean;
    message?: string;
    data?: GraphdbVO;
  }

}