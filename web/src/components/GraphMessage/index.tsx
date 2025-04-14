import { useEffect } from "react"
import {
    Graph
} from "@antv/g6";
import { IAttachedMessageItem } from "@/interfaces";
import { createRoot } from "react-dom/client";


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
                edges: edges
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
                autoFit: "center",
                node: {
                    style: {
                        labelText: (d) => d?.label,
                    },
                },
                edge: {
                    style: {
                        labelText: (d) => d?.label,
                        endArrow: true,
                        labelFontSize: 10,
                        labelBackgroundFill: "#fff",
                        labelBackground: true,
                    },
                },
                layout: {
                    type: "force",
                    linkDistance: 50,
                    clustering: true,
                    nodeClusterBy: 'cluster',
                    clusterNodeStrength: 70,
                },
                behaviors: ['zoom-canvas', 'drag-canvas', "click-select",],
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

    return <div id={`graph_${message?.id}`} style={{
        border: '1px solid #ccc',
        margin: 16
    }} />

}

export default GraphMessage