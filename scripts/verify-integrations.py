#!/usr/bin/env python3
"""
Health checker for TARS integrations.

Reads reference/integrations.md to find configured integrations and tests:
- http-api: Checks if base_url is reachable
- cli: Checks if CLI tool exists
- mcp: Reports as check_mcp_servers (can't verify from script)
- not_configured: Reports as not_configured

Uses only Python standard library.
Output: JSON report with status per integration.
"""

import sys
import json
import os
import re
import shutil
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path


def parse_integrations_md(file_path):
    """Parse integrations.md to extract integration configurations.

    Returns a list of integration dicts with:
    - category, provider, type, status, required, base_url (if applicable)
    """
    integrations = []

    if not os.path.exists(file_path):
        return integrations

    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except Exception as e:
        return integrations

    # Split by H2 headers (##)
    sections = re.split(r'^## ', content, flags=re.MULTILINE)

    for section in sections[1:]:  # Skip content before first ##
        lines = section.split('\n')

        # First line is the header (integration name)
        if not lines:
            continue

        header = lines[0].strip()

        # Parse key-value pairs from the section
        integration = {'provider': header}

        for line in lines[1:]:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Parse "key: value" format
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()

                if key in ['category', 'provider', 'type', 'status', 'required', 'base_url']:
                    integration[key] = value
            elif line.startswith('- '):
                # Skip bullet points
                continue
            else:
                # If line doesn't match expected format, might be description
                continue

        # Only include if we have at least category and status
        if 'category' in integration and 'status' in integration:
            # Set defaults if not provided
            if 'type' not in integration:
                integration['type'] = 'unknown'
            if 'required' not in integration:
                integration['required'] = 'false'

            integrations.append(integration)

    return integrations


def check_http_api(base_url):
    """Check if HTTP API is reachable.

    Returns tuple of (status, detail_message)
    """
    if not base_url:
        return 'error', 'No base_url provided'

    try:
        # Add http:// if not present
        url = base_url if base_url.startswith('http') else f'http://{base_url}'

        # Create a request with a short timeout
        request = urllib.request.Request(url)
        request.add_header('User-Agent', 'TARS-Integration-Checker/1.0')

        with urllib.request.urlopen(request, timeout=5) as response:
            if response.status < 400:
                return 'ok', f'HTTP {response.status}'
            else:
                return 'error', f'HTTP {response.status}'
    except urllib.error.HTTPError as e:
        # Server is reachable but returned an error
        return 'error', f'HTTP {e.code}'
    except urllib.error.URLError as e:
        return 'error', f'Connection error: {str(e.reason)[:50]}'
    except Exception as e:
        return 'error', f'Error: {str(e)[:50]}'


def check_cli(tool_name):
    """Check if CLI tool exists using which.

    Returns tuple of (status, detail_message)
    """
    if not tool_name:
        return 'error', 'No tool name provided'

    try:
        # Use shutil.which to find the tool
        path = shutil.which(tool_name)
        if path:
            return 'ok', f'Found at {path}'
        else:
            return 'error', f'Tool not found in PATH'
    except Exception as e:
        return 'error', f'Error: {str(e)[:50]}'


def check_integration(integration):
    """Check the health of a single integration.

    Returns a result dict with health status and detail.
    """
    status = integration.get('status', 'not_configured')
    integration_type = integration.get('type', 'unknown')

    # If not configured, report as such
    if status == 'not_configured':
        return {
            'health': 'not_configured',
            'detail': 'Integration not configured'
        }

    # Check based on type
    if integration_type == 'http-api':
        base_url = integration.get('base_url', '')
        health, detail = check_http_api(base_url)
        return {'health': health, 'detail': detail}

    elif integration_type == 'cli':
        # Try both provider name and common variations
        tool_name = integration.get('provider', '')
        health, detail = check_cli(tool_name)
        return {'health': health, 'detail': detail}

    elif integration_type == 'mcp':
        return {
            'health': 'check_mcp_servers',
            'detail': 'MCP discovery happens at runtime'
        }

    else:
        return {
            'health': 'error',
            'detail': f'Unknown integration type: {integration_type}'
        }


def main():
    # Get workspace path from argument or use current directory
    workspace = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    workspace = os.path.abspath(workspace)

    integrations_file = os.path.join(workspace, 'reference', 'integrations.md')

    # Parse integrations
    integrations_list = parse_integrations_md(integrations_file)

    # Check each integration
    results = []
    for integration in integrations_list:
        result = check_integration(integration)

        integration_result = {
            'category': integration.get('category', 'unknown'),
            'provider': integration.get('provider', 'unknown'),
            'type': integration.get('type', 'unknown'),
            'status': integration.get('status', 'unknown'),
            'health': result['health'],
        }

        if result['detail']:
            integration_result['detail'] = result['detail']

        results.append(integration_result)

    # Calculate summary
    total = len(results)
    configured = sum(1 for r in results if r['status'] == 'configured')
    healthy = sum(1 for r in results if r['health'] == 'ok')
    errors = sum(1 for r in results if r['health'] == 'error')
    not_configured = sum(1 for r in results if r['health'] == 'not_configured')

    # Build report
    report = {
        'workspace': workspace,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'integrations': results,
        'summary': {
            'total': total,
            'configured': configured,
            'healthy': healthy,
            'errors': errors,
            'not_configured': not_configured
        }
    }

    # Output JSON
    print(json.dumps(report, indent=2))

    # Exit with error code if there are errors
    return 1 if errors > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
