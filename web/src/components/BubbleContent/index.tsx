import useIntlConfig from "@/hooks/useIntlConfig";
import { CheckOutlined, CloseCircleTwoTone, LoadingOutlined } from "@ant-design/icons";
import { ThoughtChain, ThoughtChainItem, XStream } from "@ant-design/x";
import { Card } from "antd";
import { throttle } from "lodash";
import { useMemo, useState, useEffect } from "react";

interface BubbleContentProps {
  status?: string,
  content: string;
  message: API.ChatVO;
}

const BubbleContent: React.FC<BubbleContentProps> = ({ status, content, message }) => {
  const { formatMessage } = useIntlConfig();
  const [thinks, setThinks] = useState<any>([]);
  const getStatusIcon = (status: ThoughtChainItem['status']) => {
    switch (status) {
      case 'success':
        return <CheckOutlined />;
      case 'error':
        return <CloseCircleTwoTone />;
      case 'pending':
        return <LoadingOutlined spin />;
      default:
        return undefined;
    }
  }


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
  }, 2000);

  useEffect(() => {
    getThink()
  }, [message])

  const items: ThoughtChainItem[] = useMemo(() => {
    const thinkingStatus = status !== 'FINISHED' ? 'pending' : 'success'
    const steps: ThoughtChainItem[] = [
      {
        title: "策划",
        description: '基于通用框架生成回答',
        status: 'success' as ThoughtChainItem['status'],
        icon: getStatusIcon('success'),
      },
      {
        title: "分析",
        status: (thinkingStatus) as ThoughtChainItem['status'],
        description: <ol>
          {thinks.map((think: any) => (
            <>
              <div key={`${think?.jobId}_goal`}><pre style={{ background: 'rgba(201, 201, 201, 0.1)' }}>{think?.goal}</pre></div>
              {
                think?.payload && <div key={`${think?.jobId}_payload`}>
                  <pre style={{ background: 'rgba(201, 201, 201, 0.1)' }}>{think?.payload}</pre>
                </div>
              }
            </>
          ))}
        </ol>,
        icon: getStatusIcon(thinkingStatus),
      }
    ]

    if (status === 'FINISHED') {
      steps.push({
        title: "回答",
        status: 'success' as const,
        icon: getStatusIcon('success'),
        description: '',
      })
    }
    return steps;
  }, [message, thinks, status])

  return <div style={{ textAlign: 'left' }}>
    {
      content !== 'STOP' && <Card style={{ border: 'unset' }}>
        <ThoughtChain items={items} />
      </Card>
    }
    {
      content && (status === 'FINISHED' || content === 'STOP') && <pre style={{ padding: 20 }}>{content === 'STOP' ? formatMessage('home.stop') : content}</pre>
    }
  </div>
}

export default BubbleContent;

