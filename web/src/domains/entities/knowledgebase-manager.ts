import { useRequest } from "@umijs/max"
import services from "../services";
import { useImmer } from "use-immer";

export const useKnowledgebaseEntity = () => {
    const [knowledgebaseEntity, updateKnowledgebaseEntity] = useImmer<{
        knowledgebase: any[],
        knowledgebaseDetail: any,
    }>({
        knowledgebase: [],
        knowledgebaseDetail: {},
    });

    // 上传文件
    const { run: runUploadFile, loading: loadingUploadFile } = useRequest(services.uploadFile, {
        manual: true,
    });


    // 编辑知识库
    const { run: runEditKnowledgebase, loading: loadingEditKnowledgebase } = useRequest(services.editKnowledgebase, {
        manual: true,
    });

    // 删除文件
    const { run: runDeleteFile, loading: loadingDeleteFile } = useRequest(services.deleteFile, {
        manual: true,
    });

    // 根据 id 获取知识库详情
    const { run: runGetKnowledgebaseById, loading: loadingGetKnowledgebaseById } = useRequest(services.getKnowledgebaseById, {
        manual: true,
    });

    // 获取所有知识库   
    const { run: runGetKnowledgebases, loading: loadingGetKnowledgebases } = useRequest(services.getKnowledgebases, {
        manual: true,
    });

    //  删除知识库
    const { run: runDeleteKnowledgebase, loading: loadingDeleteKnowledgebase } = useRequest(services.deleteKnowledgebase, {
        manual: true,
    });


    const getKnowledgebaseList = () => {
        runGetKnowledgebases().then((res) => {
            updateKnowledgebaseEntity((draft) => {
                draft.knowledgebase = res?.data || [];
            });
        });
    }

    const getKnowledgebaseDetail = (id: string) => {
        runGetKnowledgebaseById({ knowledgebases_id: id }).then((res) => {
            updateKnowledgebaseEntity((draft) => {
                draft.knowledgebaseDetail = res?.data || {};
            });
        });
    }



    return {
        knowledgebaseEntity,
        runUploadFile,
        loadingUploadFile,
        runEditKnowledgebase,
        loadingEditKnowledgebase,
        runDeleteFile,
        loadingDeleteFile,
        runGetKnowledgebaseById,
        loadingGetKnowledgebaseById,
        getKnowledgebaseList,
        getKnowledgebaseDetail,
        loadingGetKnowledgebases,
        runDeleteKnowledgebase,
        loadingDeleteKnowledgebase,
    }
}