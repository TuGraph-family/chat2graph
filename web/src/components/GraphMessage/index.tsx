import { useEffect } from "react"
import {
    Graph
} from "@antv/g6";
import { IAttachedMessageItem } from "@/interfaces";
import { createRoot } from "react-dom/client";
import styles from './index.less'


interface GraphMessageProps {
    message: IAttachedMessageItem
}

const GraphMessage: React.FC<GraphMessageProps> = ({
    message
}) => {

    const formatGraphData = (payload?: string) => {
        if (!payload) return {}
        try {
            const { vertices, edges } = JSON.parse(payload)
            return {
                nodes: vertices,
                edges: edges?.map(item => {
                    return {
                        ...item,
                        id: `${item?.source}_${item?.target}_${item?.label}`
                    }
                })
            }
        } catch (error) {
            console.error('formatGraphData' + error)
        }
    }

    const getTooltipContent = (record) => {
        const { properties } = record[0]
        const mountNode = document.createElement("div");
        const root = createRoot(mountNode);
        root.render(
            <div>
                {Object.entries(properties).map(([key, value]) => (
                    <div key={key}>{key}: {value || '-'}</div>
                ))}
            </div>
        );
        return mountNode;
    }

    useEffect(() => {
        try {
            const graph = new Graph({
                container: `graph_${message?.id}`,
                data: formatGraphData(message?.payload),
                height: 400,
                animation: false,
                autoResize: true,
                autoFit: 'view',
                node: {
                    style: {
                        labelText: (d) => d?.label,
                        labelFontSize: 8,
                    },
                },
                edge: {
                    style: {
                        labelText: (d) => d?.label,
                        endArrow: true,
                        labelFontSize: 8,
                        labelBackgroundFill: "#fff",
                        labelBackground: true,
                    },
                },
                layout: {
                    type: "force",
                    linkDistance: 300,
                    clustering: true,
                    preventOverlap: true,
                    nodeClusterBy: 'cluster',
                    clusterNodeStrength: 70,
                    nodeSize: 20
                },
                behaviors: ['zoom-canvas', 'drag-canvas', "click-select",],
                transforms: ['process-parallel-edges'],
                plugins: [
                    {
                        type: "tooltip",
                        key: "tooltip",
                        trigger: "click",
                        enterable: true,
                        getContent: (_, record: Record<string, any>) =>
                            getTooltipContent(record),
                    },
                ]
            })

            graph.render()
        } catch (e) {
            console.error('GraphMessage:' + e)
        }
    }, [])

    return <div>
        <div id={`graph_${message?.id}`} className={styles['graph']} />
        <div className={styles['graph_description']}>{message?.graph_description}</div>
    </div>

}

export default GraphMessage