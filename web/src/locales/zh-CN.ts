
export default {
  knowledgebase: {
    home: {
      title: '知识库管理',
      subTitle1: '全局知识库',
      subTitle2: '会话知识库',
      subTitle3: 'AI常识',
      remove: '清空知识库',
      removeConfirm: '将会清空知识库的全部内容，影响对应会话的输出，请确定是否清空？',
      edit: '编辑知识库',
      name: '知识库名称',
      description: '知识库描述',
      nameRequired: '请输入知识库名称',
    },
    detail: {
      breadcrumb1: "知识库",
      breadcrumb2: "知识库详情",
      label1: "创建人",
      label2: "文档名",
      label3: "文件类型",
      label4: "数据大小",
      label5: "状态",
      label6: "更新时间",
      label7: "操作",
      addFile: "添加本地文件",
      step1: "上传本地文件",
      step2: "数据处理配置",
      upload: {
        title: "点击上传或拖拽文件到这里",
        description: "支持PDF、TXT、DOC、DOCX、MD，文件大小不超过20MB",
        required: "请上传文件",
        errorSize: "文件大小不能超过20MB",
      },
      configRequired: "请配置数据处理参数",
      removeFile: "文档删除后会影响对应会话的输出，请确定是否删除？",
      success: '添加成功',
      fail: '添加失败',
      pending: '添加中',
      jsonTip: '请输入有效的 JSON 格式',
      local: '本地文件'

    },
    docs: '文档数',
  },
  database: {
    title: '图数据库管理',
    columns: {
      name: '图数据库名',
      ip: 'IP地址',
      default: '默认图项目',
      status: '可用状态',
      updateTime: '更新时间',
      operation: '操作',
      defaultTag: '默认',
      host: '图数据库地址',
    },

    deleteConfirm: '请确定是否删除图数据库{name}？',
    modal: {
      title1: '新建图数据库',
      title2: '编辑图数据库',
      label0: '图数据库名称',
      placeholder0: '请输入图数据库名称',
      label1: '数据库类型',
      placeholder1: '请选择数据库类型',
      label2: 'Host地址',
      placeholder2: '请输入Host地址',
      label3: 'Port',
      placeholder3: '请输入 Port',
      label4: '用户名',
      placeholder4: '请输入用户名',
      label5: '密码',
      placeholder5: '请输入密码',
      label6: '默认图项目',
      placeholder6: '请输入默认图项目名',
      label7: '描述',
      placeholder7: '请输入描述'
    },
  },
  actions: {
    new: '新建',
    delete: '删除',
    next: "下一步",
    ok: "确定",
    cancel: "取消",
    edit: '编辑',
    setDefault: '设置为默认',
  },
  home: {
    collapse: '打开边栏',
    expand: '收起边栏',
    openNewConversation: '开启新对话',
    newConversation: '新对话',
    tips: '仅展示最近 10 条对话',
    manager: '前往管理后台',
    model: '建模专家',
    exportData: '导数专家',
    query: '查询专家',
    placeholderPromptsTitle: '试试这样问',
    placeholderPromptsItems1: '图是什么？',
    placeholderPromptsItems2: '怎么用 ISO/GQL 查询一个点？',
    title: 'Hi，我是小图',
    description: '关于图的问题，欢迎和我沟通。',
    rename: '重命名',
    delete: '删除',
    deleteConversation: '删除对话',
    deleteConversationConfirm: '删除后无法恢复，是否继续删除？',
    deleteConversationSuccess: '删除成功',
    confirm: '确认',
    cancel: '取消',
    noResult: '暂未搜索到',
    attachment: '附件',
    placeholder: '请输入问题',
    stop: '思考已停止',
    send: '发送 ⏎',
    thinks: {
      thinking: '思考中...',
      finished: '思考完成',
      planning: '策划',
      planningDesc: 'Graph 专家们将合作解决您的问题',
      answer: '回答',
      minutes: '分',
      seconds: '秒',
      analyze: '分析'
    }
  }
}

