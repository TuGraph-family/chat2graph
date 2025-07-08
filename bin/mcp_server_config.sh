#!/usr/bin/env bash

# MCP tools configuration
# format: "name:port:command"
# for example: "npx @playwright/mcp@latest --port 8931"
# --convert--> "playwright:8931:npx @playwright/mcp@latest"
mcp_tools_config=(
    "playwright:8931:npx @playwright/mcp@latest --isolated"
)

get_mcp_name() {
    echo "$1" | cut -d: -f1
}

get_mcp_port() {
    echo "$1" | cut -d: -f2
}

get_mcp_command() {
    echo "$1" | cut -d: -f3-
}
