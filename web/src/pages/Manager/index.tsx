import { Button, Layout, Menu } from 'antd';
import styles from './index.less';
import { MenuProps } from 'antd/lib';
import Knowledgebase from '@/pages/Knowledgebase';
import { history, useLocation } from 'umi';
import KnowledgebaseDetail from '@/pages/KnowledgebaseDetail';
import useIntlConfig from '@/hooks/useIntlConfig';
import { historyPushLinkAt } from '@/utils/link';
import Graphdb from '@/pages/Graphdb';
import Language from '@/components/Language';
import { ArrowLeftOutlined, FolderOutlined, ReadOutlined } from '@ant-design/icons';
import logoSrc from '@/assets/logo.png';

const { Sider, Content } = Layout

type MenuItem = Required<MenuProps>['items'][number];

const Manage = () => {
  const location = useLocation();
  const path = location.pathname
  const { formatMessage } = useIntlConfig()
  const items: MenuItem[] = [
    { key: '/manager/knowledgebase', icon: <FolderOutlined />, label: formatMessage('knowledgebase.home.title'), title: formatMessage('knowledgebase.home.title') },
    { key: '/manager/graphdb', icon: <ReadOutlined />, label: formatMessage('database.title'), title: formatMessage('database.title') },
  ]

  const managerRoutes: { path: string, component: JSX.Element }[] = [
    {
      path: '/manager/knowledgebase',
      component: <Knowledgebase />
    },
    {
      path: '/manager/graphdb',
      component: <Graphdb />
    },
    {
      path: '/manager/knowledgebase/detail',
      component: <KnowledgebaseDetail />
    }
  ]

  return <div className={styles['manager-container']}>
    <Language />
    <div className={styles['manager-content']}>
      <Layout>
        <Sider width={200} className={styles['manager-sider']}>
          <div className={styles['manager-logo-container']}>
            <img src={logoSrc} />
            <span>Chat2Graph</span>
          </div>
          <Menu
            mode="inline"
            selectedKeys={[path.split('/').slice(0, 3).join('/')]}
            onSelect={({ key }) => {
              history.push(historyPushLinkAt(key))
            }}
            items={items} />
          {/* TODO: 暂无用户体系 */}
          {/*   <div className={styles['manager-user']}>
            <div className={styles['manager-user-avatar']}>
              <img src="https://mdn.alipayobjects.com/huamei_aw9spf/afts/img/A*GEZpQKlz_IUAAAAAAAAAAAAAeiKXAQ/original" alt="" />
            </div>
            <div className={styles['manager-user-info']}>
              <div className={styles['manager-user-name']}>用户名</div>
              <div className={styles['manager-user-email']}>yonghuyouxiang@ak.com</div>
            </div>
          </div> */}
        </Sider>
        <Layout style={{ padding: '24px' }}>
          <Content>
            {managerRoutes.find(route => route.path === path)?.component}
          </Content>
        </Layout>
      </Layout>
    </div>
  </div>
}

export default Manage