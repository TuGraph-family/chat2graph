import { useRequest } from "@umijs/max"
import services from '../services';
import { useImmer } from 'use-immer';

export const useDatabaseEntity = () => {
    const [databaseEntity, setDatabaseEntity] = useImmer<{
        databaseList: any[],
        databaseDetail: any,
    }>({
        databaseList: [],
        databaseDetail: {},
    })

    // 获取所有图数据库
    const {
        run: runGetGraphdbs,
        loading: loadingGetGraphdbs,
    } = useRequest(services.getGraphdbs, {
        manual: true,
    });

    // 创建图数据库
    const {
        run: runCreateGraphdbs,
        loading: loadingCreateGraphdbs,
    } = useRequest(services.createGraphdbs, {
        manual: true,
    });

    // 根据 id 获取图数据库详情
    const {
        run: runGetGraphdbById,
        loading: loadingGetGraphdbById,
    } = useRequest(services.getGraphdbById, {
        manual: true,
    });

    // 删除图数据库
    const {
        run: runDeleteGraphdbs,
        loading: loadingDeleteGraphdbs,
    } = useRequest(services.deleteGraphdbs, {
        manual: true,
    });

    // 更新图数据库
    const {
        run: runUpdateGraphdbs,
        loading: loadingUpdateGraphdbs,
    } = useRequest(services.updateGraphdbs, {
        manual: true,
    });

    const getDatabaseList = async () => {
        const res = await runGetGraphdbs()
        setDatabaseEntity((draft) => {
            draft.databaseList = res?.data || []
        })
    }

    const getDatabaseDetail = async (id: string) => {
        const res = await runGetGraphdbById({ graph_db_id: id })
        setDatabaseEntity((draft) => {
            draft.databaseDetail = res.data
        })
    }

    return {
        databaseEntity,
        getDatabaseList,
        loadingGetGraphdbs,
        runCreateGraphdbs,
        loadingCreateGraphdbs,
        getDatabaseDetail,
        loadingGetGraphdbById,
        runDeleteGraphdbs,
        loadingDeleteGraphdbs,
        runUpdateGraphdbs,
        loadingUpdateGraphdbs,
    }
}