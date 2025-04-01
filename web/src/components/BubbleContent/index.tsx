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
  const [lines, setLines] = useState<string[]>([]);
  const [job, setJob] = useState<any>([]);
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

  function mockReadableStream(streams: string[]) {

    return new ReadableStream({
      async start(controller) {
        for (const chunk of streams) {
          await new Promise((resolve) => { setTimeout(resolve, 500) });
          controller.enqueue(new TextEncoder().encode(chunk));
        }
        controller.close();
      },
    });
  }

  async function readStream(streams: string[]) {
    // 🌟 Read the stream
    for await (const chunk of XStream({
      readableStream: mockReadableStream(streams),
      transformStream: new TransformStream<string, string>({
        transform(chunk, controller) {
          controller.enqueue(chunk);
        },
      }),
    })) {
      setLines((pre) => Array.from(new Set([...pre, chunk])));
    }
  }

  const getThink = throttle(() => {
    const finishedThinks: any[] = []
    message?.thinking?.filter(item => !job?.includes(item?.job?.id) && item?.status === 'FINISHED')?.forEach(item => {
      setJob((pre) => [...pre, item?.job?.id])
      finishedThinks.push(item?.job?.goal, item?.payload)
    })
    if (finishedThinks?.length) {
      readStream(finishedThinks)
    }
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
          {lines.map((line, index) => (
            <div key={index}><pre style={{ background: 'rgba(201, 201, 201, 0.1)' }}>{line}</pre></div>
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
  }, [message, lines, status])

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

