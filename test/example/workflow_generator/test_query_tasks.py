from app.core.workflow.dataset_synthesis.task_subtypes import GraphTaskTypesInfo

query_tasks_infos = GraphTaskTypesInfo()
print(query_tasks_infos.get_tasks_info())
print(query_tasks_infos.get_count_info())
# query_tasks_infos.get_count_info()