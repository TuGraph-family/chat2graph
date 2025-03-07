import { Layout, Menu } from 'antd';
import styles from './index.less';
import { MenuProps } from 'antd/lib';
import { FolderOutlined, PieChartOutlined } from '@ant-design/icons';
import GraphDatabase from '@/pages/GraphDatabase';
import Books from '@/pages/Books';
import { history, useLocation } from 'umi';
import BooksDetail from '@/pages/BookDeatil';


const { Sider, Content } = Layout

type MenuItem = Required<MenuProps>['items'][number];

const Manage = () => {

    const location = useLocation();
    const path = location.pathname


    const items: MenuItem[] = [
        { key: '/manager/books', icon: <PieChartOutlined />, label: '知识库管理' },
        { key: '/manager/graphdata', icon: <FolderOutlined />, label: '图数据库管理' },
    ]

    const componentMap: Record<string, JSX.Element> = {
        '/manager/books': <Books />,
        '/manager/graphdata': <GraphDatabase />,
        '/manager/books/detail': <BooksDetail />
    }

    console.log(path.split('/').slice(0, 2).join('/'))
    return <div className={styles['manager-container']}>
        <div className={styles['manager-content']}>
            <Layout>
                <Sider width={300} className={styles['manager-sider']}>
                    <img src="https://mdn.alipayobjects.com/huamei_aw9spf/afts/img/A*NYPKQrkHc3IAAAAAAAAAAAAAeiKXAQ/original" alt="" className={styles['manager-logo']} />
                    <Menu
                        mode="inline"
                        selectedKeys={[path.split('/').slice(0, 3).join('/')]}
                        onSelect={({ key }) => {
                            history.push(key)
                        }}
                        items={items} />
                    <div className={styles['manager-user']}>
                        <div className={styles['manager-user-avatar']}>
                            <img src="https://mdn.alipayobjects.com/huamei_aw9spf/afts/img/A*GEZpQKlz_IUAAAAAAAAAAAAAeiKXAQ/original" alt="" />
                        </div>
                        <div className={styles['manager-user-info']}>
                            <div className={styles['manager-user-name']}>用户名</div>
                            <div className={styles['manager-user-email']}>yonghuyouxiang@ak.com</div>
                        </div>
                    </div>
                </Sider>
                <Layout style={{ padding: '24px' }}>
                    <Content>
                        {componentMap[path]}
                    </Content>
                </Layout>
            </Layout>

        </div>



    </div>
}

export default Manage