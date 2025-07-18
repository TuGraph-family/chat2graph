from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import yaml  # type: ignore

from app.core.common.type import ReasonerType, ToolGroupType, ToolType, WorkflowPlatformType
from app.core.toolkit.tool_config import McpConfig, McpTransportConfig, ToolGroupConfig


@dataclass
class ToolConfig:
    """Tool configuration data class"""

    name: str
    type: ToolType


@dataclass
class LocalToolConfig(ToolConfig):
    """Local tool configuration data class"""

    module_path: str


@dataclass
class ActionConfig:
    """Action configuration data class"""

    name: str
    desc: str
    tools: List[Union[ToolConfig, ToolGroupConfig]] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class OperatorConfig:
    """Operator configuration data class"""

    instruction: str
    output_schema: str
    actions: List[str] = field(default_factory=list)


@dataclass
class ReasonerConfig:
    """Reasoner configuration data class"""

    type: ReasonerType = ReasonerType.DUAL


@dataclass
class ProfileConfig:
    """Agent profile configuration data class"""

    name: str
    desc: str = ""


@dataclass
class LeaderConfig:
    """Leader configuration data class"""

    actions: List[ActionConfig] = field(default_factory=list)


@dataclass
class ExpertConfig:
    """Expert configuration data class"""

    profile: ProfileConfig
    workflow: List[List["OperatorConfig"]] = field(default_factory=list)


@dataclass
class AppConfig:
    """App configuration data class"""

    name: str
    desc: str = ""
    version: str = "0.0.1"


@dataclass
class PluginConfig:
    """Plugin configuration data class"""

    workflow_platform: Optional[str] = None

    def get_workflow_platform_type(self) -> Optional[WorkflowPlatformType]:
        """Get the platform type enum value"""
        if self.workflow_platform:
            return WorkflowPlatformType(self.workflow_platform)
        return None


@dataclass
class AgenticConfig:
    """AgenticService configuration data class"""

    app: AppConfig
    plugin: PluginConfig = field(default_factory=PluginConfig)
    reasoner: ReasonerConfig = field(default_factory=ReasonerConfig)
    toolkit: List[List[ActionConfig]] = field(default_factory=list)
    leader: LeaderConfig = field(default_factory=LeaderConfig)
    experts: List[ExpertConfig] = field(default_factory=list)
    knowledgebase: Dict[str, Any] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=dict)
    env: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, yaml_path: Union[str, Path], encoding: str = "utf-8") -> "AgenticConfig":
        """Parse the YAML configuration file and create an AgenticConfig object."""
        with open(yaml_path, encoding=encoding) as f:
            config_dict = yaml.safe_load(f)

        return cls._create_from_dict(config_dict)

    @classmethod
    def _create_from_dict(cls, config_dict: Dict[str, Any]) -> "AgenticConfig":
        """Create an AgenticConfig object from a dictionary."""
        # app configuration
        app_dict = config_dict.get("app", {})
        app_config = AppConfig(
            name=app_dict.get("name", ""),
            desc=app_dict.get("desc", ""),
            version=app_dict.get("version", "0.0.1"),
        )

        # plugin configuration
        plugin_dict = config_dict.get("plugin", {})
        plugin_config = PluginConfig(workflow_platform=plugin_dict.get("workflow_platform"))

        # reasoner configuration
        reasoner_dict = config_dict.get("reasoner", {})
        reasoner_config = ReasonerConfig(type=ReasonerType(reasoner_dict.get("type", "DUAL")))

        # toolkit configuration (step 1): create all tool configurations
        tools_dict: Dict[str, Union[ToolConfig, ToolGroupConfig]] = {}
        for tool_dict in config_dict.get("tools", []):
            if not isinstance(tool_dict, dict):
                raise ValueError(f"Tool configuration '{tool_dict}' must be a dictionary.")

            tool_type: str = tool_dict.get("type", ToolType.LOCAL_TOOL.value)
            if tool_type == ToolType.LOCAL_TOOL.value:
                tool_config: Union[ToolConfig, ToolGroupConfig] = LocalToolConfig(
                    name=tool_dict.get("name", ""),
                    type=ToolType.LOCAL_TOOL,
                    module_path=tool_dict.get("module_path", ""),
                )
            elif tool_type == ToolGroupType.MCP.value:
                tool_config = McpConfig(
                    type=ToolGroupType.MCP,
                    name=tool_dict.get("name", ""),
                    transport_config=McpTransportConfig.from_dict(
                        tool_dict.get("mcp_transport_config", {})
                    ),
                )
            else:
                raise ValueError(
                    f"Tool configuration '{tool_dict}' must be either LOCAL_TOOL or MCP."
                )
            tools_dict[tool_config.name] = tool_config

        # toolkit configuration (step 2): create all action configurations
        actions_dict: Dict[str, ActionConfig] = {}
        action_tools_map: Dict[str, List[str]] = {}  # action_name -> tool_names

        for action_dict in config_dict.get("actions", []):
            if not isinstance(action_dict, dict):
                continue

            tool_refs = []
            for tool_ref in action_dict.get("tools", []):
                if isinstance(tool_ref, dict) and "name" in tool_ref:
                    tool_refs.append(tool_ref["name"])

            action_config = ActionConfig(
                name=action_dict.get("name", ""),
                desc=action_dict.get("desc", ""),
                tools=[],
                id=action_dict.get("id", str(uuid4())),
            )
            actions_dict[action_config.name] = action_config
            action_tools_map[action_config.name] = tool_refs

        # toolkit configuration (step 3): connect tool configurations to actions'
        for action_name, tool_names in action_tools_map.items():
            action = actions_dict[action_name]
            for tool_name in tool_names:
                if tool_name in tools_dict:
                    action.tools.append(tools_dict[tool_name])

        # toolkit configuration (step 4): handle all action chains
        toolkit: List[List[ActionConfig]] = []
        for action_chain in config_dict.get("toolkit", []):
            chain: List[ActionConfig] = []
            for action_ref in action_chain:
                action_name = ""
                assert isinstance(action_ref, dict) and "name" in action_ref
                action_name = action_ref["name"]

                if action_name and action_name in actions_dict:
                    chain.append(actions_dict[action_name])

            if chain:
                toolkit.append(chain)

        # leader configuration
        leader_dict = config_dict.get("leader", {})
        leader_actions: List[ActionConfig] = []
        for action_ref in leader_dict.get("actions", []):
            if isinstance(action_ref, dict) and action_ref["name"] in actions_dict:
                leader_actions.append(actions_dict[action_ref["name"]])
        leader_config = LeaderConfig(actions=leader_actions)

        # expert configuration
        experts: List[ExpertConfig] = []
        for expert_dict in config_dict.get("experts", []):
            if not isinstance(expert_dict, dict):
                raise ValueError("Expert configuration must be a dictionary.")

            # profile configuration
            profile_dict: Dict[str, Any] = expert_dict.get("profile", {})
            profile = ProfileConfig(
                name=profile_dict.get("name", ""), desc=profile_dict.get("desc", "")
            )

            # workflow configuration
            workflow_chains: List[List[OperatorConfig]] = []
            for op_chains in expert_dict.get("workflow", []):
                op_configs: List[OperatorConfig] = []
                for op_ref in op_chains:
                    assert (
                        isinstance(op_ref, dict)
                        and "instruction" in op_ref
                        and "output_schema" in op_ref
                        and "actions" in op_ref
                    )

                    # actions configuration in operator
                    action_names: List[str] = []
                    for action_ref in op_ref["actions"]:
                        if isinstance(action_ref, dict) and "name" in action_ref:
                            action_names.append(action_ref["name"])
                    op_configs.append(
                        OperatorConfig(
                            instruction=op_ref["instruction"],
                            output_schema=op_ref["output_schema"],
                            actions=action_names,
                        )
                    )

                if op_configs:
                    workflow_chains.append(op_configs)

            experts.append(ExpertConfig(profile=profile, workflow=workflow_chains))

        return cls(
            app=app_config,
            plugin=plugin_config,
            reasoner=reasoner_config,
            toolkit=toolkit,
            leader=leader_config,
            experts=experts,
            knowledgebase=config_dict.get("knowledgebase", {}),
            memory=config_dict.get("memory", {}),
            env=config_dict.get("env", {}),
        )

    def _export_to_dict(self) -> Dict[str, Any]:
        """Export the configuration to a dictionary."""
        # app exportation
        result: Dict[str, Any] = {
            "app": {"name": self.app.name, "desc": self.app.desc, "version": self.app.version}
        }

        # plugin exportation
        if self.plugin.workflow_platform:
            result["plugin"] = {"workflow_platform": self.plugin.workflow_platform}

        # reasoner exportation
        if self.reasoner.type:
            result["reasoner"] = {"type": self.reasoner.type.value}

        # collect all tools and actions
        all_tools: Dict[str, Union[ToolConfig, ToolGroupConfig]] = {}
        all_actions: Dict[str, ActionConfig] = {}
        for action_chain in self.toolkit:
            for action in action_chain:
                all_actions[action.name] = action
                for tool in action.tools:
                    all_tools[tool.name] = tool

        # tools exportation
        result["tools"] = []
        for tool in all_tools.values():
            if isinstance(tool, LocalToolConfig):
                tool_dict: Dict[str, Any] = {
                    "name": tool.name,
                    "type": tool.type.value,
                    "module_path": tool.module_path,
                }
            elif isinstance(tool, McpConfig):
                tool_dict = {
                    "name": tool.name,
                    "type": tool.type.value,
                    "mcp_transport_config": tool.transport_config.to_dict(),
                }
            else:
                raise ValueError(f"Unknown tool type: {type(tool)}")
            result["tools"].append(tool_dict)

        # actions exportation
        result["actions"] = []
        for action in all_actions.values():
            action_dict: Dict[str, Any] = {
                "name": action.name,
                "desc": action.desc,
                "id": action.id,
            }
            if action.tools:
                action_tools_list: List[Dict[str, Any]] = []
                for tool in action.tools:
                    if isinstance(tool, LocalToolConfig):
                        action_tools_list.append(
                            {
                                "name": tool.name,
                                "type": tool.type.value,
                                "module_path": tool.module_path,
                            }
                        )
                    elif isinstance(tool, McpConfig):
                        action_tools_list.append(
                            {
                                "name": tool.name,
                                "type": tool.type.value,
                                "mcp_transport_config": tool.transport_config.to_dict(),
                            }
                        )
                    else:
                        raise ValueError(f"Unknown tool type: {type(tool)}")
                action_dict["tools"] = action_tools_list

            result["actions"].append(action_dict)

        # toolkit exportation
        result["toolkit"] = []
        for action_chain in self.toolkit:
            chain_action_dicts: List[Dict[str, Any]] = []
            for action in action_chain:
                if action.name in all_actions:
                    chain_action_dict: Dict[str, Any] = {
                        "name": action.name,
                        "desc": action.desc,
                        "id": all_actions[action.name].id,
                    }
                    if action.tools:
                        action_tools_list = []
                        for tool in action.tools:
                            if isinstance(tool, LocalToolConfig):
                                action_tools_list.append(
                                    {
                                        "name": tool.name,
                                        "type": tool.type.value,
                                        "module_path": tool.module_path,
                                    }
                                )
                            elif isinstance(tool, McpConfig):
                                action_tools_list.append(
                                    {
                                        "name": tool.name,
                                        "type": tool.type.value,
                                        "mcp_transport_config": tool.transport_config.to_dict(),
                                    }
                                )
                            else:
                                raise ValueError(f"Unknown tool type: {type(tool)}")
                        chain_action_dict["tools"] = action_tools_list
                    chain_action_dicts.append(chain_action_dict)
            if chain_action_dicts:
                result["toolkit"].append(chain_action_dicts)

        # leader exportation
        result["leader"] = {"actions": []}
        for action in self.leader.actions:
            if action.name in all_actions:
                action_dict = {
                    "name": action.name,
                    "desc": action.desc,
                    "id": all_actions[action.name].id,
                }
                result["leader"]["actions"].append(action_dict)

        # experts exportation
        result["experts"] = []
        for expert in self.experts:
            expert_dict: Dict[str, Any] = {
                "profile": {"name": expert.profile.name},
            }

            if expert.profile.desc:
                expert_dict["profile"]["desc"] = expert.profile.desc

            # workflow exportation
            if expert.workflow:
                expert_dict["workflow"] = []
                for op_chain in expert.workflow:
                    op_chain_list = []
                    for op in op_chain:
                        # operator exportation
                        op_dict: Dict[str, Any] = {
                            "instruction": op.instruction,
                            "output_schema": op.output_schema,
                        }
                        if op.actions:
                            op_action_dicts: List[Dict[str, Any]] = []
                            for action_name in op.actions:
                                if action_name in all_actions:
                                    action = all_actions[action_name]
                                    op_action_dict: Dict[str, Any] = {
                                        "name": action.name,
                                        "desc": action.desc,
                                        "id": action.id,
                                    }
                                    if action.tools:
                                        op_action_tools_list: List[Dict[str, Any]] = []
                                        for tool in action.tools:
                                            if isinstance(tool, LocalToolConfig):
                                                op_action_tools_list.append(
                                                    {
                                                        "name": tool.name,
                                                        "type": tool.type.value,
                                                        "module_path": tool.module_path,
                                                    }
                                                )
                                            elif isinstance(tool, McpConfig):
                                                op_action_tools_list.append(
                                                    {
                                                        "name": tool.name,
                                                        "type": tool.type.value,
                                                        "mcp_transport_config": tool.transport_config.to_dict(),  # noqa: E501
                                                    }
                                                )
                                            else:
                                                raise ValueError(f"Unknown tool type: {type(tool)}")
                                        op_action_dict["tools"] = op_action_tools_list
                                    op_action_dicts.append(op_action_dict)
                            op_dict["actions"] = op_action_dicts
                        op_chain_list.append(op_dict)
                    expert_dict["workflow"].append(op_chain_list)

            result["experts"].append(expert_dict)

        # other exportations
        if self.knowledgebase:
            result["knowledgebase"] = self.knowledgebase
        if self.memory:
            result["memory"] = self.memory
        if self.env:
            result["env"] = self.env

        return result

    def export_yaml(self, yaml_path: Union[str, Path], encoding: str = "utf-8") -> Optional[str]:
        """Export the configuration to a YAML file or return as a string.

        Args:
            yaml_path (Union[str, Path]): Exported YAML file path. If None, returns the YAML string.
            encoding (str): File encoding. Default is "utf-8".

        Returns:
            Optional[str]: YAML string if yaml_path is None, otherwise None.
        """
        config_dict: Dict[str, Any] = self._export_to_dict()

        yaml_str = yaml.dump(
            config_dict,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
            width=100,
        )

        if yaml_path:
            with open(yaml_path, "w", encoding=encoding) as f:
                f.write(yaml_str)
            return None

        return yaml_str
