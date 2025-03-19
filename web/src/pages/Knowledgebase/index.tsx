import { DeleteOutlined, EllipsisOutlined } from '@ant-design/icons';
import { Badge, Dropdown, Popconfirm, Typography } from 'antd';
import styles from './index.less';
import KnowledgebasesTable from './components/KnowledgebasesTable';
import useIntlConfig from '@/hooks/useIntlConfig';
import { useEffect, useMemo } from 'react';
import { useKnowledgebaseEntity } from '@/domains/entities/knowledgebase-manager';

const Knowledgebase = () => {
  const { formatMessage } = useIntlConfig();
  const { getKnowledgebaseList, loadingGetKnowledgebases, knowledgebaseEntity } = useKnowledgebaseEntity();

  const knowledgebaseTotal = useMemo(() => {
    if (knowledgebaseEntity.knowledgebase.length > 0) {
        // 计算知识库总数
        const total = knowledgebaseEntity.knowledgebase.reduce((acc, curr) => acc + (curr?.file_count || 0), 0)
        return total
    }
    return 0
  }, [knowledgebaseEntity.knowledgebase]);

  const items = [{
    label: <Popconfirm
      title={formatMessage('knowledgebase.home.remove')}
      description={formatMessage('knowledgebase.home.removeConfirm')}
      onConfirm={() => { }}
      icon={<DeleteOutlined />}
    >
      {formatMessage('knowledgebase.home.remove')}1
    </Popconfirm>,
    icon: <DeleteOutlined />,
    key: 'delete',
    onClick: (e: any) => {
      e?.domEvent.stopPropagation()
      // TODO: 待实现
    }
  }];

  useEffect(() => {
    getKnowledgebaseList()
  }, []);

  return <div>
    <div className={styles['title']}>{formatMessage('knowledgebase.home.title')}</div>
    <div className={styles['knowledge-base-total']}>
      <div className={styles['knowledge-base-total-header']}>
        <div className={styles['knowledge-base-total-header-title']}>
          {formatMessage('knowledgebase.home.subTitle1')}
          <span className={styles['knowledge-base-total-header-count']}>文档数：<strong>{knowledgebaseTotal}</strong></span>
        </div>
        <Dropdown menu={{ items }}>
        <EllipsisOutlined style={{ fontSize: 20 }} />
        </Dropdown>
      </div>

      <div className={styles['knowledge-base-total-content']}>
        <Typography.Paragraph className={styles['knowledge-base-total-content-name']} ellipsis={{rows: 2, tooltip: ''}}>
        人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识人工智能常识
        </Typography.Paragraph>
        {/* <div className={styles['knowledge-base-total-content-info']}>
          <h2>{knowledgebaseTotal}</h2>
          <div className={styles['knowledge-base-total-content-info-desc']}>{formatMessage('knowledgebase.docs')}</div>
        </div> */}
      </div>
    </div>

    <KnowledgebasesTable
      onRefresh={getKnowledgebaseList}
      formatMessage={formatMessage}
      dataSource={knowledgebaseEntity?.knowledgebase}
      loading={loadingGetKnowledgebases}
    />
  </div>
}

export default Knowledgebase