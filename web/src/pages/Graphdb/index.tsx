import { message } from 'antd'
import styles from './index.less'
import { useImmer } from 'use-immer'
import GraphDataModal from './components/GraphDataModal'
import { useDatabaseEntity } from '@/domains/entities/database-manager'
import useIntlConfig from '@/hooks/useIntlConfig';
import AsyncTable from '@/components/AsyncTable'
import { useEffect } from 'react'
import { useGraphDBColumns } from '@/hooks/useGraphDBColumns'

const Graphdb: React.FC = () => {
  const [state, setState] = useImmer<{
    open: boolean
    editId: string | null
  }>({
    open: false,
    editId: null,
  })
  const { open, editId, } = state
  const { getDatabaseList, loadingGetGraphdbs, databaseEntity, runDeleteGraphdbs, loadingDeleteGraphdbs, runUpdateGraphdbs, loadingUpdateGraphdbs } = useDatabaseEntity();
  const { formatMessage } = useIntlConfig();

  const onRefresh = () => {
    getDatabaseList()
  };

  const onOpenModal = (id?: string) => {
    setState((draft) => {
      draft.open = true
      draft.editId = id || null;
    })
  }

  const onDeleteGraphDatabase = async (id: string) => {
    const res = await runDeleteGraphdbs({
      graph_db_id: id
    })
    if (res?.success) {
      onRefresh()
      message.success(res?.message)
    } else {
      message.error(res?.message)
    }
  }

  const setDefaultGraphDatabase = async (record: Record<string, any>) => {
    const { id, ...rest } = record
    const res = await runUpdateGraphdbs({ session_id: id }, {
      ...rest,
      is_default_db: true
    })
    if (res?.success) {
      onRefresh()
      message.success(res?.message)
    } else {
      message.error(res?.message)
    }
  }

  useEffect(() => {
    getDatabaseList()
  }, [])


  const { columns } = useGraphDBColumns({
    styles,
    onDeleteGraphDatabase,
    setDefaultGraphDatabase,
    onOpenModal,
  })




  return <div className={styles['graph-database']}>
    <div className={styles['graph-database-title']}>{formatMessage('database.title')}</div>
    <AsyncTable
      dataSource={databaseEntity?.databaseList}
      loading={loadingGetGraphdbs || loadingDeleteGraphdbs || loadingUpdateGraphdbs}
      columns={columns}
      extra={[
        { key: 'search', searchKey: 'name' },
        { key: 'add', onClick: () => onOpenModal() }
      ]}
    />

    <GraphDataModal
      editId={editId}
      open={open}
      onClose={() => setState((draft) => { draft.open = false; draft.editId = null })}
      onFinish={onRefresh}
      formatMessage={formatMessage}
    />
  </div>
}

export default Graphdb
