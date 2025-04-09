import useIntlConfig from "@/hooks/useIntlConfig";
import { Card, Skeleton, Spin, Steps } from "antd";
import { throttle } from "lodash";
import { useMemo, useEffect, useState } from "react";
import logoSrc from '@/assets/logo.png';
import styles from './index.less';
import { useImmer } from "use-immer";

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
    diffTime: number
  }>({
    thinks: [],
    startTime: 0,
    diffTime: 0
  })

  const { startTime, diffTime } = state;



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
    const newThinks = message?.thinking?.map(item => {
      return {
        jobId: item?.job?.id,
        status: item?.status,
        goal: item?.job?.goal,
        payload: item?.status === 'FINISHED' ? item?.payload : ''
      }
    })
    setThinks(updateCachedData(thinks, newThinks))
    setState(draft => {
      if (status === 'CREATED' || status === 'RUNNING') {
        draft.diffTime = new Date().getTime() - startTime
      }
    })

  }, 2000);

  useEffect(() => {
    setState(draft => {
      draft.startTime = new Date().getTime()
    })
  }, [])

  useEffect(() => {
    getThink()
  }, [message])

  const renderTime = () => {
    if (!diffTime) {
      return null
    }
    const minutes = Math.floor(diffTime / 60000);
    const seconds = Math.floor((diffTime % 60000) / 1000);
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
          {thinks.map((think: any, idx: number) => (
            <>
              <div key={`${think?.jobId}_goal`} className={styles['step-thinks-title']}>
                {`${idx + 1}.${think?.goal}`}
              </div>
              {
                think?.payload ? <div key={`${think?.jobId}_payload`} className={styles['step-thinks-message']}>
                  <pre>{think?.payload}</pre>
                </div> : <Skeleton paragraph={{ rows: 1 }} active />
              }
            </>
          ))}
          {
            status !== 'FINISHED' && thinks?.length === 0 && <Skeleton paragraph={{ rows: 2 }} active />
          }
        </div>,
        icon: <img src={logoSrc} className={styles['step-icon']} />,
      }
    ]

    if (status === 'FINISHED') {
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
      content !== 'STOP' && <Card style={{ border: 'unset' }}>
        <div className={styles['bubble-content-status']}>
          <Spin percent={status === 'FINISHED' ? 100 : 50} />
          <span className={styles['bubble-content-status-text']}>{status === 'FINISHED' ? formatMessage('home.thinks.finished') : formatMessage('home.thinks.thinking')}</span>
        </div>
        <Steps items={items} direction="vertical" />
      </Card>
    }
    {
      content && (status === 'FINISHED' || content === 'STOP') && <pre className={styles['bubble-content-message']}>{content === 'STOP' ? formatMessage('home.stop') : content}</pre>
    }
  </div>
}

export default BubbleContent;

