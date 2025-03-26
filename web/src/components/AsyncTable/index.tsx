import { Button, Input, Space, Table, TableProps } from 'antd'
import styles from './index.less'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons'
import { debounce } from 'lodash'
import useIntlConfig from '@/hooks/useIntlConfig'
import { useSearchPagination } from '@/hooks/useSearchPagination'

interface AsyncTableProps extends TableProps<any> {
  dataSource: any[],
  loading: boolean,
  columns: any[],
  extra: any[],
}

const AsyncTable: React.FC<AsyncTableProps> = ({
  dataSource,
  loading,
  columns,
  extra,
  ...otherProps
}) => {
  const { formatMessage } = useIntlConfig()
  const {
    paginatedData,
    total,
    pageSize,
    currentPage,
    setSearchText,
    setCurrentPage,
    setPageSize
  } = useSearchPagination({
    data: dataSource || [],
    searchKey: extra?.find((item: any) => item.key === 'search')?.searchKey || '',
    defaultPageSize: 10
  });

  const onSearch = debounce((value: string) => {
    setSearchText(value)
  }, 500)

  const renderExtra = () => {
    if (!extra) {
      return null
    }
    return <div className={styles['async-table-extra']}>
      <Space>
        {
          extra?.map((item: any) => {
            switch (item.key) {
              case 'search': return <Input placeholder='Search' prefix={<SearchOutlined />} onChange={(e) => {
                onSearch(e.target.value)
              }} />
              case 'add': return <Button type="primary" onClick={item.onClick}><PlusOutlined />{formatMessage('actions.new')}</Button>
            }
            return item
          })
        }
      </Space>
    </div>
  }

  return <div>
    {renderExtra()}
    <div className={styles['async-table-table']}>
      <Table
        loading={loading}
        columns={columns}
        dataSource={paginatedData}
        onChange={(pagination) => {
          setCurrentPage(pagination.current || 1)
          setPageSize(pagination.pageSize || 10)
        }}
        pagination={{
          total: total,
          current: currentPage,
          pageSize,
        }}
        {...otherProps}
      />
    </div>
  </div>
}

export default AsyncTable