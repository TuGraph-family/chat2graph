import { CheckOutlined, CloseCircleTwoTone, LoadingOutlined } from "@ant-design/icons";
import { ThoughtChain, ThoughtChainItem, XStream } from "@ant-design/x";
import { Card } from "antd";
import { useMemo, useState, useEffect } from "react";

interface BubbleContentProps {
  status: string,
  content: string;
  message: API.ChatVO;
}

const BubbleContent: React.FC<BubbleContentProps> = ({ status, content, message }) => {

  const [lines, setLines] = useState<string[]>([]);
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

  function mockReadableStream() {

    const list = message?.thinking?.map(item => item.payload) || []
    return new ReadableStream({
      async start(controller) {
        for (const chunk of list) {
          await new Promise((resolve) => { setTimeout(resolve, 500) });
          controller.enqueue(new TextEncoder().encode(chunk));
        }
        controller.close();
      },
    });
  }

  async function readStream() {
    // 🌟 Read the stream
    for await (const chunk of XStream({
      readableStream: mockReadableStream(),
      transformStream: new TransformStream<string, string>({
        transform(chunk, controller) {
          controller.enqueue(chunk);
        },
      }),
    })) {
      setLines((pre) => [...pre, chunk]);
    }
  }
  useEffect(() => {
    readStream()
  }, [])

  const items: ThoughtChainItem[] = useMemo(() => {
    const steps: ThoughtChainItem[] = [
      {
        title: "策划",
        description: '基于通用框架生成回答',
        status: 'success' as ThoughtChainItem['status'],
        icon: getStatusIcon('success'),
      },
      {
        title: "分析",
        status: (message?.thinking ? 'success' : 'pending') as ThoughtChainItem['status'],
        description: <ol>
          {lines.map((line, index) => (
            <div key={index}><pre style={{ background: 'rgba(201, 201, 201, 0.1)' }}>{line}</pre></div>
          ))}
        </ol>,
        icon: getStatusIcon(message?.thinking ? 'success' : 'pending'),
      }
    ]

    if (status !== 'loading') {
      steps.push({
        title: "回答",
        status: 'success' as const,
        icon: getStatusIcon('success'),
        description: '',
      })
    }
    return steps;
  }, [message, lines])

  return <div style={{ textAlign: 'left' }}>
    <Card style={{ border: 'unset' }}>
      <ThoughtChain items={items} />
    </Card>
    {
      content && <pre style={{ padding: 20 }}>{content}</pre>
    }
  </div>
}

export default BubbleContent;

