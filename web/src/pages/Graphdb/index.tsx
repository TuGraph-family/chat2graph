import { Button, message, Popconfirm, Tag } from 'antd'
import styles from './index.less'
import { useImmer } from 'use-immer'
import GraphDataModal from './components/GraphDataModal'
import { useDatabaseEntity } from '@/domains/entities/database-manager'
import useIntlConfig from '@/hooks/useIntlConfig';
import AsyncTable from '@/components/AsyncTable'
import { useEffect } from 'react'



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

  const onOpenModal = (id = null) => {
    setState((draft) => {
      draft.open = true
      draft.editId = id
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


  const columns = [
    {
      title: formatMessage('database.columns.name'),
      dataIndex: 'name',
      render: (text: string, record: any) => {
        return <div className={styles['graph-database-name']}>
          {text}
          {record.is_default_db && <Tag style={{ marginLeft: 10 }} bordered={false} color="processing">
            {formatMessage('database.columns.defaultTag')}
          </Tag>}
        </div>
      }
    },
    {
      title: formatMessage('database.columns.ip'),
      dataIndex: 'ip',
    },
    {
      title: formatMessage('database.columns.default'),
      dataIndex: 'desc',
    },
    {
      title: formatMessage('database.columns.status'),
      dataIndex: 'stauts',
      render: (text: boolean) => {
        return text ? <Tag color="cyan" bordered={false}>可用</Tag> : <Tag color="error" bordered={false}>不可用</Tag>
      }
    },
    {
      title: formatMessage('database.columns.updateTime'),
      dataIndex: 'updateTime',
    },
    {
      title: formatMessage('database.columns.operation'),
      dataIndex: 'operation',
      render: (text: string, record: any) => {
        return <div className={styles['graph-database-operation']}>
          <Button type="link" onClick={() => onOpenModal(record.id)} >{formatMessage('actions.edit')}</Button>
          <Popconfirm
            title={formatMessage('database.deleteConfirm', { name: record.name })}
            onConfirm={() => onDeleteGraphDatabase(record.id)}
          >
            <Button type="link" disabled={record.is_default_db}>{formatMessage('actions.delete')}</Button>
          </Popconfirm>
          <Button type="link" disabled={record.is_default_db} onClick={() => setDefaultGraphDatabase(record)}>{formatMessage('actions.setDefault')}</Button>
        </div>
      }
    },
  ]

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
      is_default_db={!databaseEntity?.databaseList?.length}
    />
  </div>
}

export default Graphdb
