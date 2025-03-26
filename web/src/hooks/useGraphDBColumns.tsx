import useIntlConfig from "@/hooks/useIntlConfig";
import { Button, Popconfirm, Tag } from "antd";


interface IUseGraphDBClumuns {
  styles: any;
  onOpenModal: (id?: string) => void;
  onDeleteGraphDatabase: (id: string) => void;
  setDefaultGraphDatabase: (record: any) => void;
}

export const useGraphDBColumns = ({
  styles,
  onOpenModal,
  onDeleteGraphDatabase,
  setDefaultGraphDatabase,
}: IUseGraphDBClumuns) => {

  const { formatMessage } = useIntlConfig();
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

  return {
    columns
  }
}