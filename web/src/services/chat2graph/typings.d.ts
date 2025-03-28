
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



  interface Result_Knowledgebases_ {
    success?: boolean;
    message?: string;
    data?: {
      global_knowledge_base?: KnowledgebaseVO,
      local_knowledge_base?: Array<KnowledgebaseVO>;
    };
  }

  interface Result_Knowledgebase_ {
    success?: boolean;
    message?: string;
    data?: KnowledgebaseVO;
  }

  interface Result_Upload_ {
    success?: boolean;
    message?: string;
    data?: {
      file_id?: string;
    };
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

  interface Result_JobIds_ {
    success?: boolean;
    message?: string;
    data?: {
      id?: string;
    };
  }

  interface MessageVO {
    id?: string;
    message: ChatVO;
    status?: string;
  }

  interface ChatVO {
    id?: string,
    job_id?: string,
    message_type?: string,
    others?: any,
    role?: string,
    session_id?: string,
    assigned_expert_name?: string | null,
    timestamp?: string,
    payload?: string,
    status?: string,
    thinking?: any
    attached_messages?: any
  }

  interface Result_Chat_ {
    success?: boolean;
    message?: string;
    data?: ChatVO;
  }

  interface QuestionVO {
    message?: ChatVO;
  }


  interface MetricsVO {
    job_id: string,
    status: 'CREATED' | 'RUNNING' | 'FINISHED' | 'FAILED' | 'STOPPED',
    duration: number,
    tokens: number
  }

  interface AnwerVO {
    message?: ChatVO;
    metrics?: MetricsVO;
  }


  interface JobVO {
    answer: AnwerVO & {
      thinking?: Array<AnwerVO>;
    };
    question: QuestionVO;
  }

  interface Result_Job_ {
    success?: boolean;
    message?: string;
    data?: JobVO;
  }

  interface Result_Messages_ {
    success?: boolean;
    message?: string;
    data?: Array<JobVO>;
  }

}