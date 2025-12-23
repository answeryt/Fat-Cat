# -*- coding: utf-8 -*-
"""Content extraction and filtering layer."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class ExtractedContent:
    title: str
    summary: str
    key_data: dict[str, Any]
    url: str | None = None


class ContentExtractor:
    def extract_from_web_scrape(self, raw_content: str, url: str) -> ExtractedContent:
        cleaned = self._remove_noise(raw_content)
        title = self._extract_title(cleaned, raw_content)
        main_content = self._extract_main_content(cleaned)
        key_data = self._extract_key_data(main_content, url)
        summary = self._generate_summary(main_content)
        
        return ExtractedContent(
            title=title,
            summary=summary,
            key_data=key_data,
            url=url
        )
    
    def _remove_noise(self, content: str) -> str:
        if not content:
            return ""
        
        lines = content.split('\n')
        cleaned_lines = []
        skip_patterns = [
            r'We owe you an explanation',
            r'Please select an amount',
            r'Donate.*monthly',
            r'This page has been blocked',
            r'ERR_BLOCKED_BY_CLIENT',
            r'Continue with Google',
            r'Continue with apple',
            r'Sign up for.*newsletter',
            r'Having trouble logging in',
            r'Username\s*Continue',
            r'Email address\s*Submit',
            r'SPONSORED',
            r'Advertise With Us',
            r'Jump to content',
            r'All topics',
            r'Go to IMDbPro',
            r'Problems donating',
            r'Frequently asked questions',
            r'Where your donation goes',
            r'Other ways to give',
            r'I already donated',
            r'We never sell your information',
            r'By continuing, you agree',
            r'Terms and Policies',
            r'Privacy Policy',
            r'Sign me up',
            r'No thanks',
            r'Maybe later',
            r'Welcome back',
            r'Login successful',
            r'Let\'s keep in touch',
            r'Rotten Tomatoes Newsletter',
            r'Trending on RT',
            r'DOWNLOAD THE APP',
            r'CONTINUE IN BROWSER',
        ]
        
        in_noise_block = False
        noise_block_patterns = [
            (r'We owe you an explanation', r'Continue|Maybe later|I already donated'),
            (r'Please select an amount', r'Continue|Maybe later|Donate'),
            (r'This page has been blocked', r'Reload|Back'),
            (r'Username\s*Continue', r'Continue|Sign in'),
            (r'Welcome back', r'Continue|Login successful'),
            (r'Let\'s keep in touch', r'Sign me up|No thanks'),
        ]
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped or len(line_stripped) < 3:
                continue
            
            if re.match(r'^!\[', line_stripped):
                continue
            
            if re.match(r'^<', line_stripped) and re.search(r'</', line_stripped):
                continue
            
            is_noise = False
            for pattern in skip_patterns:
                if re.search(pattern, line_stripped, re.IGNORECASE):
                    is_noise = True
                    break
            
            if is_noise:
                continue
            
            block_matched = False
            for start_pattern, end_pattern in noise_block_patterns:
                if re.search(start_pattern, line_stripped, re.IGNORECASE):
                    in_noise_block = True
                    is_noise = True
                    block_matched = True
                    break
                if in_noise_block and re.search(end_pattern, line_stripped, re.IGNORECASE):
                    in_noise_block = False
                    is_noise = True
                    block_matched = True
                    break
            
            if in_noise_block and not block_matched:
                continue
            
            if not is_noise and not in_noise_block:
                cleaned_lines.append(line)
        
        cleaned = '\n'.join(cleaned_lines)
        
        cleaned = re.sub(r'\n{4,}', '\n\n\n', cleaned)
        
        return cleaned
    
    def _extract_title(self, cleaned: str, original: str) -> str:
        title_match = re.search(r'^Title:\s*(.+)$', cleaned, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()
        
        h1_match = re.search(r'^#\s+(.+)$', cleaned, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()
        
        return "Untitled"
    
    def _extract_main_content(self, content: str) -> str:
        if not content:
            return ""
        
        lines = content.split('\n')
        main_lines = []
        skip_until_content = True
        content_started = False
        
        for line in lines:
            line_stripped = line.strip()
            
            if skip_until_content:
                if re.match(r'^(Title:|#\s+|##\s+)', line_stripped):
                    skip_until_content = False
                    content_started = True
                    if line_stripped.startswith('Title:'):
                        continue
                else:
                    continue
            
            if not content_started:
                continue
            
            if len(line_stripped) < 3:
                if main_lines and main_lines[-1].strip():
                    main_lines.append("")
                continue
            
            if re.match(r'^!\[', line_stripped):
                continue
            
            if re.match(r'^<', line_stripped):
                continue
            
            main_lines.append(line)
        
        main_content = '\n'.join(main_lines).strip()
        
        if len(main_content) > 3000:
            paragraphs = main_content.split('\n\n')
            main_content = '\n\n'.join(paragraphs[:15])
            main_content += '\n\n[... 内容已截断，完整内容见原始数据 ...]'
        
        return main_content
    
    def _extract_key_data(self, content: str, url: str) -> dict[str, Any]:
        key_data = {}
        
        if 'wikipedia.org' in (url or ''):
            key_data['source_type'] = 'wikipedia'
            infobox_match = re.search(r'\|\s*([^|]+)\s*\|\s*([^|]+)', content)
            if infobox_match:
                key_data['has_infobox'] = True
        
        if 'imdb.com' in (url or ''):
            key_data['source_type'] = 'imdb'
            cast_match = re.search(r'(Cast|Writer|Director)', content, re.IGNORECASE)
            if cast_match:
                key_data['has_credits'] = True
        
        return key_data
    
    def _generate_summary(self, content: str) -> str:
        if not content or len(content.strip()) < 50:
            return "内容为空或过短"
        
        lines = content.split('\n')
        summary_lines = []
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) > 20:
                summary_lines.append(line)
        
        summary = ' '.join(summary_lines)
        if len(summary) > 300:
            summary = summary[:300] + '...'
        
        return summary
    
    def extract_tool_call_summary(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
        tool_output: str | None,
        tool_error: str | None,
    ) -> str:
        if tool_error:
            return f"工具调用失败: {tool_error}"
        
        if tool_name == 'web_search':
            query = tool_args.get('query', '')
            max_results = tool_args.get('max_results', 5)
            if tool_output:
                result_count = len(re.findall(r'^\d+\.', tool_output, re.MULTILINE))
                return f"搜索查询: '{query}' | 返回 {result_count} 个结果"
            return f"搜索查询: '{query}'"
        
        if tool_name == 'web_scrape':
            url = tool_args.get('url', '')
            if tool_output:
                extracted = self.extract_from_web_scrape(tool_output, url)
                return f"抓取页面: {url} | 标题: {extracted.title} | 摘要: {extracted.summary[:100]}"
            return f"抓取页面: {url}"
        
        return f"工具: {tool_name} | 参数: {list(tool_args.keys())}"

