import useIntlConfig from "@/hooks/useIntlConfig";
import { Card, Collapse, Skeleton, Spin, Steps } from "antd";
import { throttle } from "lodash";
import { useMemo, useEffect, useState } from "react";
import logoSrc from '@/assets/logo.png';
import styles from './index.less';
import { useImmer } from "use-immer";
import { getTimeDifference } from "@/utils/getTimeDifference";
import { MESSAGE_TYPE, MESSAGE_TYPE_TIPS } from "@/constants";
import ReactMarkdown from 'react-markdown';
import gfm from 'remark-gfm';
import ThinkCollapse from "@/components/ThinkCollapse";
import ThinkStatus from "@/components/ThinkStatus";
import { DownOutlined, UpOutlined } from "@ant-design/icons";

interface BubbleContentProps {
  status?: string,
  content: string;
  message: API.ChatVO;
}

const BubbleContent: React.FC<BubbleContentProps> = ({ status, content, message }) => {
  const { formatMessage } = useIntlConfig();
  const [thinks, setThinks] = useState<any>([]);
  const [state, setState] = useImmer<{
    thinks: any[],
    startTime: number,
    diffTime: number,
    percent: number,
  }>({
    thinks: [],
    startTime: new Date().getTime(),
    diffTime: 0,
    percent: 20
  })

  const { startTime, diffTime, percent } = state;



  const updateCachedData = (cachedData, newData) => {
    const cachedMap = new Map(cachedData.map(item => [item.jobId, item]));
    newData.forEach(newItem => {
      const cachedItem = cachedMap.get(newItem.jobId);
      if (cachedItem) {
        cachedItem.goal = newItem.goal ?? cachedItem.goal;
        cachedItem.payload = newItem.payload ?? cachedItem.payload;
      } else {
        cachedMap.set(newItem.jobId, { ...newItem });
      }
    });
    return Array.from(cachedMap.values());
  }

  const getThink = throttle(() => {
    console.log(message)
    let finidshed = 0
    const newThinks = message?.thinking?.map(item => {
      if (item?.status === MESSAGE_TYPE.FINISHED) {
        finidshed += 1
      }
      return {
        jobId: item?.job?.id,
        status: item?.status,
        goal: item?.job?.goal,
        payload: item?.status === MESSAGE_TYPE.FINISHED ? item?.payload : '',
        assigned_expert_name: item?.message?.assigned_expert_name
      }
    })

    setThinks(updateCachedData(thinks, newThinks))
    setState(draft => {
      if (status === MESSAGE_TYPE.CREATED || status === MESSAGE_TYPE.RUNNING) {
        draft.diffTime = new Date().getTime() - startTime
      }
      draft.percent = 20 + 60 * (finidshed / message?.thinking?.length)
    })
  }, 2000);


  useEffect(() => {
    getThink()
  }, [message])

  const renderTime = () => {
    if (!diffTime) {
      return null
    }
    const { minutes, seconds } = getTimeDifference(diffTime)

    return `${minutes ? minutes + formatMessage('home.thinks.minutes') : ''}${seconds + formatMessage('home.thinks.seconds')}`
  }


  const items = useMemo(() => {
    const steps = [
      {
        title: <div className={styles['title']}>
          <div className={styles['title-content']}>{formatMessage('home.thinks.planning')}</div>
          {
            diffTime ? <div className={styles['title-extra']}>{2 + formatMessage('home.thinks.seconds')}</div> : null
          }

        </div>,
        description: <div>{formatMessage('home.thinks.planningDesc')}</div>,
        icon: <img src={logoSrc} className={styles['step-icon']} />,
      },
      {
        title: <div className={styles['title']}>
          <div className={styles['title-content']}>{formatMessage('home.thinks.analyze')}</div>
          <div className={styles['title-extra']}>{
            renderTime()
          }
          </div>
        </div>,
        description: <div className={styles['step-thinks']}>
          {thinks.map((think: any) => <ThinkCollapse key={`${think?.jobId}_goal`} think={think} />)}
          {
            status !== MESSAGE_TYPE.FINISHED && thinks?.length === 0 && <Skeleton paragraph={{ rows: 2 }} active />
          }
        </div>,
        icon: <img src={logoSrc} className={styles['step-icon']} />,
      }
    ]

    if (status === MESSAGE_TYPE.FINISHED) {
      setState(draft => {
        draft.percent = 100
      })
      steps.push({
        title: <div className={styles['title']}>
          <div className={styles['title-content']}>{formatMessage('home.thinks.answer')}</div>
        </div>,
        icon: <img src={logoSrc} className={styles['step-icon']} />,
        description: <></>,
      })
    }
    return steps;
  }, [message, thinks, status])

  return <div className={styles['bubble-content']}>
    {

      <Collapse
        collapsible="header"
        defaultActiveKey={['1']}
        expandIconPosition="end"
        expandIcon={({ isActive }) => isActive ? <UpOutlined style={{ color: '#6a6b71' }} /> : <DownOutlined style={{ color: '#6a6b71' }} />}
        items={[
          {
            key: '1',
            label: <div className={styles['bubble-content-header']}>
              <div className={styles['bubble-content-status']}>
                {/* <Spin percent={status === MESSAGE_TYPE.FINISHED ? 100 : 50} /> */}
                <ThinkStatus status={status} percent={percent} />
                <span className={styles['bubble-content-status-text']}>{formatMessage(MESSAGE_TYPE_TIPS[status])}</span>
              </div>
              {/* <div onClick={() => { setState(draft => { draft.open = !draft.open }) }}>
          {
            open ? <UpOutlined /> : <DownOutlined />
          }
        </div> */}
            </div>,
            children: content !== 'STOP' && ![MESSAGE_TYPE.FAILED, MESSAGE_TYPE.STOPPED].includes(status) && <Steps items={items} direction="vertical" />
            ,
          },
        ]}
      />
      // <Card style={{ border: 'unset' }}>

      //   {
      //     content !== 'STOP' && ![MESSAGE_TYPE.FAILED, MESSAGE_TYPE.STOPPED].includes(status) && <Steps items={items} direction="vertical" />
      //   }
      // </Card>
    }
    {
      content
      && (status === MESSAGE_TYPE.FINISHED || content === MESSAGE_TYPE.STOP || status === MESSAGE_TYPE.FAILED)
      && <div className={styles['bubble-content-message']}>
        {/* <pre className={styles['bubble-content-message']}>{content === MESSAGE_TYPE.STOP ? formatMessage('home.stop') : content}</pre> */}
        <ReactMarkdown remarkPlugins={[gfm]}>{content === MESSAGE_TYPE.STOP ? formatMessage('home.stop') : content}</ReactMarkdown>
      </div>
    }

  </div>
}

export default BubbleContent;

