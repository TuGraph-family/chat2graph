import { message, Typography } from 'antd';
import styles from './index.less';
import KnowledgebasesTable from './components/KnowledgebasesTable';
import useIntlConfig from '@/hooks/useIntlConfig';
import { useEffect } from 'react';
import { useKnowledgebaseEntity } from '@/domains/entities/knowledgebase-manager';
import { history } from 'umi'
import { historyPushLinkAt } from '@/utils/link';

const Knowledgebase = () => {
  const { formatMessage } = useIntlConfig();
  const { getKnowledgebaseList, runDeleteKnowledgebase, loadingGetKnowledgebases, knowledgebaseEntity, loadingDeleteKnowledgebase } = useKnowledgebaseEntity();

  useEffect(() => {
    getKnowledgebaseList()
  }, []);

  const onDeleteKnowledgebase = async (id: string) => {
    const res = await runDeleteKnowledgebase({
      knowledgebases_id: id
    })
    if (res) {
      message.success(res?.message)
      getKnowledgebaseList()
    }
  }

  return <div>
    <div className={styles['title']}>{formatMessage('knowledgebase.home.title')}</div>
    <div className={styles['knowledge-base-total']} onClick={() => {
      history.push(historyPushLinkAt('/manager/knowledgebase/detail', { id: knowledgebaseEntity?.global_knowledge_base?.id }))
    }}>
      <div className={styles['knowledge-base-total-header']} >
        <div className={styles['knowledge-base-total-header-title']}>
          {formatMessage('knowledgebase.home.subTitle1')}
          <span className={styles['knowledge-base-total-header-count']}>{formatMessage('knowledgebase.docs')}：<strong>{knowledgebaseEntity?.global_knowledge_base?.file_count || 0}</strong></span>
        </div>
      </div>

      <div className={styles['knowledge-base-total-content']}>
        <Typography.Paragraph className={styles['knowledge-base-total-content-name']} ellipsis={{ rows: 2, tooltip: '' }}>
          {formatMessage('knowledgebase.home.subTitle3')}
        </Typography.Paragraph>
      </div>
    </div>

    <KnowledgebasesTable
      onRefresh={getKnowledgebaseList}
      formatMessage={formatMessage}
      onDeleteKnowledgebase={onDeleteKnowledgebase}
      dataSource={knowledgebaseEntity?.knowledgebase}
      loading={loadingGetKnowledgebases || loadingDeleteKnowledgebase}
    />
  </div>
}

export default Knowledgebase