

const knowledgebaseList = [
    {
        id: "1",
        knowledge_type: "private",
        name: "图是什么？",
        session_id: "session_id_1",
        description: '12312312313123',
        file_count: 2,
        files: [
            { "name": "a.txt", "type": "local", "size": "1048kb", "status": "success", "time_stamp": 1741767769901, file_id: "05f559ce-6a60-4127-81d4-63d730baa737" },
            { "name": "b.txt", "type": "local", "size": "1048kb", "status": "success", "time_stamp": 1741767769901, file_id: "05f55555-6a60-4127-81d4-63d730baa737" },
        ]
    },
    {
        id: "2",
        knowledge_type: "private",
        name: "图是什么？",
        session_id: "session_id_2",
        file_count: 1,
        files: [
            { "name": "c.txt", "type": "local", "size": "1048kb", "status": "success", "time_stamp": 1741767769901, file_id: "05f55555-6a60-4127-81d4-63d730baa737" },
        ]
    },
    {
        id: "3",
        knowledge_type: "private",
        name: "图是什么？",
        session_id: "session_id_3",
        file_count: 1,
        files: [
            { "name": "d.txt", "type": "local", "size": "1048kb", "status": "success", "time_stamp": 1741767769901, file_id: "05f55555-6a60-4127-81d4-63d730baa737" },
        ]
    },
    {
        id: "4",
        knowledge_type: "private",
        name: "图是什么？",
        session_id: "session_id_4",
        file_count: 1,
        files: [
            { "name": "e.txt", "type": "local", "size": "1048kb", "status": "success", "time_stamp": 1741767769901, file_id: "05f55555-6a60-4127-81d4-63d730baa737" },
        ]
    },
    {
        id: "5",
        knowledge_type: "private",
        name: "图是什么？",
        session_id: "session_id_5",
        file_count: 1,
        files: [
            { "name": "f.txt", "type": "local", "size": "1048kb", "status": "success", "time_stamp": 1741767769901, file_id: "05f55555-6a60-4127-81d4-63d730baa737" },
        ]
    },
]

export default {
    '/api/knowledgebases': (req: any, res: any) => {
        res.send({
            code: 200,
            message: 'success',
            data: knowledgebaseList
        })
    },
    '/api/knowledgebases/:id': (req: any, res: any) => {
        const { id } = req.params
        const knowledgebase = knowledgebaseList.find(item => item.id === id)
        console.log(req, 'req')
        res.send({
            code: 200,
            message: 'success',
            data: knowledgebase
        })
    },
    "POST /api/files/upload": (req: any, res: any) => {
        res.send({
            code: 200,
            message: 'success',
            data: {}
        })
    }
}