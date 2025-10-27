# src/utils/html_templates.py

"""
Centralized email templates for all notification types
"""

def get_test_report_template(project_name, environment, test_name, status, details=None):
    """
    Beautiful HTML template for individual test reports
    
    Args:
        project_name: Name of the project
        environment: Test environment
        test_name: Name of the test
        status: Test status (PASS/FAIL)
        details: Additional test details
    
    Returns:
        tuple: (subject, plain_text_body, html_body)
    """
    status_color = "#22c55e" if status == "PASS" else "#ef4444"
    status_bg_color = "#dcfce7" if status == "PASS" else "#fee2e2"
    status_emoji = "✅" if status == "PASS" else "❌"
    
    subject = f"🧪 Test {status}: {test_name}"
    
    # Plain text version
    plain_text = f"""
PROJECT: {project_name}
ENVIRONMENT: {environment}
TEST: {test_name}
STATUS: {status}
TIMESTAMP: {details.get('timestamp', 'N/A') if details else 'N/A'}
DURATION: {details.get('duration', 'N/A') if details else 'N/A'}

ADDITIONAL DETAILS:
{details.get('message', 'No additional details') if details else 'No additional details'}

---
This is an automated test report from your test automation framework
Generated at {details.get('timestamp', 'N/A') if details else 'N/A'}
"""
    
    # HTML version
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px 10px 0 0;
            text-align: center;
        }}
        .content {{
            background: #f8fafc;
            padding: 25px;
            border-radius: 0 0 10px 10px;
            border: 1px solid #e2e8f0;
        }}
        .status-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
            background: {status_bg_color};
            color: {status_color};
            border: 2px solid {status_color};
        }}
        .detail-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 20px 0;
        }}
        .detail-card {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .detail-label {{
            font-size: 12px;
            color: #64748b;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}
        .detail-value {{
            font-size: 14px;
            color: #1e293b;
            font-weight: 500;
        }}
        .message-box {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #f59e0b;
            margin-top: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .footer {{
            text-align: center;
            margin-top: 25px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            color: #64748b;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin: 0; font-size: 24px;">🧪 Test Automation Report</h1>
        <p style="margin: 8px 0 0 0; opacity: 0.9;">{project_name}</p>
    </div>
    
    <div class="content">
        <div style="text-align: center; margin-bottom: 25px;">
            <span class="status-badge">
                {status_emoji} {status}
            </span>
        </div>
        
        <div style="text-align: center; margin-bottom: 25px;">
            <h2 style="color: #1e293b; margin: 0;">{test_name}</h2>
        </div>
        
        <div class="detail-grid">
            <div class="detail-card">
                <div class="detail-label">📊 Project</div>
                <div class="detail-value">{project_name}</div>
            </div>
            <div class="detail-card">
                <div class="detail-label">🌐 Environment</div>
                <div class="detail-value">{environment}</div>
            </div>
            <div class="detail-card">
                <div class="detail-label">🕐 Timestamp</div>
                <div class="detail-value">{details.get('timestamp', 'N/A') if details else 'N/A'}</div>
            </div>
            <div class="detail-card">
                <div class="detail-label">⏱️ Duration</div>
                <div class="detail-value">{details.get('duration', 'N/A') if details else 'N/A'}</div>
            </div>
        </div>
        
        <div class="message-box">
            <div class="detail-label">📝 Test Details</div>
            <div class="detail-value" style="margin-top: 10px; white-space: pre-wrap;">
                {details.get('message', 'No additional details provided') if details else 'No additional details provided'}
            </div>
        </div>
        
        <div class="footer">
            <p>This is an automated test report from your test automation framework</p>
            <p>Generated at {details.get('timestamp', 'N/A') if details else 'N/A'}</p>
        </div>
    </div>
</body>
</html>
"""
    
    return subject, plain_text, html_body


def get_html_report_template(test_results, filename=None):
    """
    Enhanced HTML report template for test suite results
    
    Args:
        test_results: Dictionary with test results data
        filename: Optional report filename
    
    Returns:
        str: Complete HTML content
    """
    total_tests = test_results.get('total', 0)
    passed_tests = test_results.get('passed', 0)
    failed_tests = test_results.get('failed', 0)
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Geo Travel Test Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: #f8fafc;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-top: 4px solid;
        }}
        .stat-total {{ border-color: #667eea; }}
        .stat-passed {{ border-color: #22c55e; }}
        .stat-failed {{ border-color: #ef4444; }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .stat-label {{
            font-size: 1.1em;
            color: #64748b;
        }}
        .success-rate {{
            text-align: center;
            margin: 30px 0;
            padding: 20px;
            background: linear-gradient(135deg, #dcfce7, #bbf7d0);
            border-radius: 8px;
        }}
        .test-details {{
            margin-top: 30px;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            color: #64748b;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Geo Travel Test Execution Report</h1>
            <p>Comprehensive test results and analytics</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card stat-total">
                <div class="stat-label">Total Tests</div>
                <div class="stat-number">{total_tests}</div>
            </div>
            <div class="stat-card stat-passed">
                <div class="stat-label">Passed</div>
                <div class="stat-number" style="color: #22c55e;">{passed_tests}</div>
            </div>
            <div class="stat-card stat-failed">
                <div class="stat-label">Failed</div>
                <div class="stat-number" style="color: #ef4444;">{failed_tests}</div>
            </div>
        </div>
        
        <div class="success-rate">
            <h2>Success Rate: {success_rate:.1f}%</h2>
            <p>{passed_tests} out of {total_tests} tests passed successfully</p>
        </div>
        
        <div class="test-details">
            <h3>📊 Execution Summary</h3>
            <p><strong>Generated:</strong> {test_results.get('timestamp', 'N/A')}</p>
            <p><strong>Environment:</strong> {test_results.get('environment', 'N/A')}</p>
            <p><strong>Duration:</strong> {test_results.get('duration', 'N/A')}</p>
        </div>
        
        <div class="footer">
            <p>Report generated automatically by Geo Travel Test Automation Framework</p>
            <p>{test_results.get('timestamp', 'N/A')}</p>
        </div>
    </div>
</body>
</html>
"""
    return html_content


def get_success_capture_template(test_name, screenshot_path=None, browser_info=None):
    """
    HTML template for success evidence capture
    
    Args:
        test_name: Name of the test
        screenshot_path: Path to screenshot (optional)
        browser_info: Browser information (optional)
    
    Returns:
        str: HTML content for success report
    """
    from datetime import datetime
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Success Report - {test_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: #f0fdf4;
            color: #333;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: white;
            padding: 25px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 25px;
        }}
        .success-badge {{
            font-size: 3em;
            margin-bottom: 10px;
        }}
        .details-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 25px 0;
        }}
        .detail-card {{
            background: #f8fafc;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #22c55e;
        }}
        .screenshot-section {{
            text-align: center;
            margin: 30px 0;
        }}
        .screenshot {{
            max-width: 100%;
            border: 2px solid #22c55e;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            color: #64748b;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="success-badge">✅</div>
            <h1>Test Successfully Completed</h1>
            <h2>{test_name}</h2>
        </div>
        
        <div class="details-grid">
            <div class="detail-card">
                <h3>📋 Test Information</h3>
                <p><strong>Test Name:</strong> {test_name}</p>
                <p><strong>Status:</strong> <span style="color: #22c55e; font-weight: bold;">SUCCESS</span></p>
                <p><strong>Timestamp:</strong> {datetime.now().isoformat()}</p>
            </div>
            
            <div class="detail-card">
                <h3>🌐 Environment Details</h3>
                <p><strong>URL:</strong> {browser_info.get('url', 'N/A') if browser_info else 'N/A'}</p>
                <p><strong>Browser:</strong> {browser_info.get('browser', 'N/A') if browser_info else 'N/A'}</p>
                <p><strong>Platform:</strong> {browser_info.get('platform', 'N/A') if browser_info else 'N/A'}</p>
            </div>
        </div>
        
        {f'''
        <div class="screenshot-section">
            <h3>📸 Success Evidence</h3>
            <img src="{screenshot_path}" alt="Success Screenshot" class="screenshot">
            <p><em>Screenshot captured at time of success</em></p>
        </div>
        ''' if screenshot_path else '<p>📸 No screenshot available</p>'}
        
        <div class="footer">
            <p>This success report was automatically generated by the test automation framework</p>
            <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>"""
    
    return html_content

def get_error_report_template(test_name, error_message, current_url="N/A", page_source="N/A", additional_info=None, timestamp=None):
    """
    Enhanced HTML template for error reports
    
    Args:
        test_name: Name of the failed test
        error_message: Error message/details
        current_url: Current page URL
        page_source: HTML page source
        additional_info: Additional context information
        timestamp: Error timestamp
    
    Returns:
        str: HTML content for error report
    """
    from datetime import datetime
    
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{test_name} - Error Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: #fef2f2;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #dc2626, #b91c1c);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .error-badge {{
            font-size: 3em;
            margin-bottom: 15px;
        }}
        .info-section {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #dc2626;
        }}
        .additional-info {{
            background: #fff3cd;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #f59e0b;
        }}
        .page-content {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #3b82f6;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }}
        .info-card {{
            background: #f8fafc;
            padding: 15px;
            border-radius: 6px;
            border-left: 3px solid #64748b;
        }}
        .error-message {{
            background: #fef2f2;
            border: 1px solid #fecaca;
            color: #dc2626;
            padding: 15px;
            border-radius: 6px;
            margin: 15px 0;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        h3 {{
            color: #1e293b;
            margin-top: 0;
        }}
        pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
            background: #1e293b;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 12px;
            max-height: 400px;
            overflow-y: auto;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            color: #64748b;
        }}
        .url-link {{
            color: #3b82f6;
            text-decoration: none;
            word-break: break-all;
        }}
        .url-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="error-badge">🚨</div>
            <h1>Test Failure Report</h1>
            <h2>{test_name}</h2>
        </div>
        
        <div class="info-section">
            <h3>📋 Test Information</h3>
            <div class="info-grid">
                <div class="info-card">
                    <strong>🧪 Test Name:</strong><br>
                    {test_name}
                </div>
                <div class="info-card">
                    <strong>🌐 URL:</strong><br>
                    <a href="{current_url}" class="url-link" target="_blank">{current_url}</a>
                </div>
                <div class="info-card">
                    <strong>🕐 Timestamp:</strong><br>
                    {timestamp}
                </div>
                <div class="info-card">
                    <strong>📊 Status:</strong><br>
                    <span style="color: #dc2626; font-weight: bold;">FAILED</span>
                </div>
            </div>
            
            <h3>❌ Error Details</h3>
            <div class="error-message">
                {error_message}
            </div>
        </div>
"""

    # Add additional information section if available
    if additional_info:
        html_content += """
        <div class="additional-info">
            <h3>📊 Additional Context</h3>
            <div class="info-grid">
"""
        for key, value in additional_info.items():
            html_content += f"""
                <div class="info-card">
                    <strong>{key}:</strong><br>
                    {value}
                </div>
"""
        html_content += """
            </div>
        </div>
"""

    # Add page source section
    html_content += f"""
        <div class="page-content">
            <h3>🌐 Page Source (First 5000 characters)</h3>
            <details>
                <summary>Click to view page source</summary>
                <pre>{page_source[:5000] + ('...' if len(page_source) > 5000 else '')}</pre>
            </details>
            <p style="color: #64748b; font-size: 12px; margin-top: 10px;">
                <em>Showing first 5000 characters. Full source available in logs.</em>
            </p>
        </div>
        
        <div class="footer">
            <p>This error report was automatically generated by the test automation framework</p>
            <p>{timestamp}</p>
        </div>
    </div>
</body>
</html>"""
    
    return html_content