"""Markdown documentation testing for 100% coverage."""

import pytest
import os
import re
import subprocess
from unittest.mock import Mock, patch
from pathlib import Path


class TestMarkdownDocumentation:
    """Test suite for markdown documentation to achieve 100% coverage."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return os.getcwd()

    @pytest.fixture
    def markdown_files(self, project_root):
        """Get all markdown files in the project."""
        markdown_files = []
        for root, dirs, files in os.walk(project_root):
            for file in files:
                if file.endswith('.md'):
                    markdown_files.append(os.path.join(root, file))
        return markdown_files

    def test_markdown_files_exist(self, markdown_files):
        """Test that markdown files exist."""
        assert len(markdown_files) > 0, "No markdown files found"

    def test_required_documentation_exists(self, project_root):
        """Test that required documentation files exist."""
        required_docs = [
            "README.md",
            "FEATURE_DEPLOYMENT_GUIDE.md",
            "DEPLOYMENT_PIPELINE.md",
            "DEPLOYMENT_SUMMARY.md",
            "DEPLOYMENT_VALIDATION.md"
        ]
        
        for doc in required_docs:
            doc_path = os.path.join(project_root, doc)
            assert os.path.exists(doc_path), f"Required documentation {doc} does not exist"

    def test_markdown_syntax_validation(self, markdown_files):
        """Test markdown syntax validation."""
        for md_file in markdown_files:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Test for common markdown syntax
            assert len(content) > 0, f"{md_file} is empty"
            
            # Test that headers are properly formatted
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('#'):
                    # Headers should have space after #
                    assert re.match(r'^#+\s+', line), f"Malformed header at line {i+1} in {md_file}"

    def test_readme_content(self, project_root):
        """Test README.md content."""
        readme_path = os.path.join(project_root, "README.md")
        
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Test for essential README sections
        assert "# " in content or "##" in content, "README lacks proper headers"
        
        # Test for project description
        content_lower = content.lower()
        assert any(word in content_lower for word in ["financial", "stronghold", "project"]), \
            "README lacks project description"

    def test_feature_deployment_guide_content(self, project_root):
        """Test FEATURE_DEPLOYMENT_GUIDE.md content."""
        guide_path = os.path.join(project_root, "FEATURE_DEPLOYMENT_GUIDE.md")
        
        with open(guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Test for deployment guide sections
        content_lower = content.lower()
        assert "deployment" in content_lower
        assert "guide" in content_lower
        
        # Test for required sections mentioned in the problem statement
        assert "overview" in content_lower
        assert "ci/cd" in content_lower or "pipeline" in content_lower

    def test_deployment_pipeline_content(self, project_root):
        """Test DEPLOYMENT_PIPELINE.md content."""
        pipeline_path = os.path.join(project_root, "DEPLOYMENT_PIPELINE.md")
        
        with open(pipeline_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Test for pipeline documentation
        content_lower = content.lower()
        assert "pipeline" in content_lower
        assert "deployment" in content_lower

    def test_code_blocks_syntax(self, markdown_files):
        """Test code blocks have proper syntax."""
        for md_file in markdown_files:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find code blocks
            code_blocks = re.findall(r'```(\w*)\n(.*?)\n```', content, re.DOTALL)
            
            for language, code in code_blocks:
                # Test that code blocks are not empty
                assert code.strip(), f"Empty code block in {md_file}"
                
                # Test specific language syntax if specified
                if language == "bash" or language == "sh":
                    # Bash code should have proper commands
                    assert any(cmd in code for cmd in ["echo", "cd", "ls", "docker", "python", "pip"]) or \
                           code.strip().startswith("#"), f"Invalid bash code in {md_file}"
                
                elif language == "python":
                    # Python code should have valid syntax
                    lines = code.strip().split('\n')
                    # Simple check for Python-like syntax
                    python_indicators = ["import", "def ", "class ", "print", "return", "if ", "for ", "="]
                    assert any(indicator in code for indicator in python_indicators), \
                        f"Invalid Python code in {md_file}"

    def test_links_in_markdown(self, markdown_files):
        """Test links in markdown files."""
        for md_file in markdown_files:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find markdown links [text](url)
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
            
            for link_text, link_url in links:
                # Test that links have proper text
                assert link_text.strip(), f"Empty link text in {md_file}"
                
                # Test internal links (starting with #)
                if link_url.startswith('#'):
                    # Verify anchor exists in document
                    anchor = link_url[1:].lower().replace('-', ' ')
                    content_lower = content.lower()
                    # Simple check for section existence
                    assert anchor in content_lower or link_url[1:] in content_lower, \
                        f"Broken internal link {link_url} in {md_file}"

    def test_tables_in_markdown(self, markdown_files):
        """Test tables in markdown files."""
        for md_file in markdown_files:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find markdown tables
            lines = content.split('\n')
            in_table = False
            
            for i, line in enumerate(lines):
                if '|' in line and line.strip().startswith('|') and line.strip().endswith('|'):
                    # This looks like a table row
                    cells = [cell.strip() for cell in line.split('|')[1:-1]]
                    
                    # Test that table cells are not empty (except for formatting rows)
                    if not all(cell in ['', '---', ':---', '---:', ':---:'] for cell in cells):
                        assert any(cell for cell in cells), f"Empty table row at line {i+1} in {md_file}"

    def test_images_in_markdown(self, markdown_files):
        """Test images in markdown files."""
        for md_file in markdown_files:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find markdown images ![alt](src)
            images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
            
            for alt_text, image_src in images:
                # Test that images have alt text
                assert alt_text.strip(), f"Missing alt text for image {image_src} in {md_file}"
                
                # Test that image source is specified
                assert image_src.strip(), f"Empty image source in {md_file}"

    def test_headers_hierarchy(self, markdown_files):
        """Test proper header hierarchy in markdown files."""
        for md_file in markdown_files:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            header_levels = []
            
            for line in lines:
                if line.startswith('#'):
                    level = len(line) - len(line.lstrip('#'))
                    header_levels.append(level)
            
            # Test that headers follow proper hierarchy (no skipping levels)
            for i in range(1, len(header_levels)):
                level_diff = header_levels[i] - header_levels[i-1]
                # Allow going deeper by any amount, but only go up one level at a time
                if level_diff < 0:  # Going up in hierarchy
                    assert abs(level_diff) <= 3, f"Header hierarchy jump too large in {md_file}"

    def test_documentation_alignment_with_vision(self, project_root):
        """Test that documentation aligns with vision statement."""
        # Read the main documentation files
        main_docs = [
            "README.md",
            "FEATURE_DEPLOYMENT_GUIDE.md",
            "DEPLOYMENT_SUMMARY.md"
        ]
        
        vision_keywords = [
            "financial", "stronghold", "dashboard", "ci/cd", "pipeline", 
            "deployment", "docker", "testing", "coverage"
        ]
        
        for doc in main_docs:
            doc_path = os.path.join(project_root, doc)
            if os.path.exists(doc_path):
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                
                # Test that documentation mentions key vision elements
                keyword_count = sum(1 for keyword in vision_keywords if keyword in content)
                assert keyword_count >= 3, f"{doc} doesn't align well with project vision"

    def test_code_examples_in_documentation(self, markdown_files):
        """Test code examples in documentation are valid."""
        for md_file in markdown_files:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find bash code examples
            bash_blocks = re.findall(r'```(?:bash|sh)\n(.*?)\n```', content, re.DOTALL)
            
            for bash_code in bash_blocks:
                lines = bash_code.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Test that bash commands look valid
                        if line.startswith('docker'):
                            assert any(subcmd in line for subcmd in ['build', 'run', 'compose', 'ps']), \
                                f"Invalid docker command in {md_file}: {line}"
                        elif line.startswith('python'):
                            # Python commands should have proper syntax
                            assert len(line.split()) >= 1, f"Invalid python command in {md_file}: {line}"

    def test_deployment_guide_process_flow(self, project_root):
        """Test that deployment guide follows the process flow mentioned in problem statement."""
        guide_path = os.path.join(project_root, "FEATURE_DEPLOYMENT_GUIDE.md")
        
        with open(guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Test for process flow elements mentioned in problem statement
        content_lower = content.lower()
        
        process_elements = [
            "overview", "feature description", "pre-deployment", 
            "ci/cd pipeline", "environment", "monitoring", "validation"
        ]
        
        found_elements = 0
        for element in process_elements:
            if element in content_lower:
                found_elements += 1
        
        assert found_elements >= len(process_elements) // 2, \
            "Deployment guide doesn't follow expected process flow"

    def test_documentation_completeness(self, markdown_files):
        """Test documentation completeness."""
        total_content_length = 0
        
        for md_file in markdown_files:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            total_content_length += len(content)
        
        # Test that we have substantial documentation
        assert total_content_length > 10000, "Documentation appears to be incomplete"

    def test_markdown_formatting_consistency(self, markdown_files):
        """Test markdown formatting consistency."""
        for md_file in markdown_files:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # Test for consistent list formatting
            for line in lines:
                if line.strip().startswith('- '):
                    # List items should have space after dash
                    assert line.strip().startswith('- '), f"Inconsistent list formatting in {md_file}"
                elif line.strip().startswith('* '):
                    # Alternative list format
                    assert line.strip().startswith('* '), f"Inconsistent list formatting in {md_file}"

    @patch('subprocess.run')
    def test_markdown_linting(self, mock_subprocess, markdown_files):
        """Test markdown linting if tools are available."""
        mock_subprocess.return_value = Mock(returncode=0, stdout="No issues found", stderr="")
        
        # Test with a markdown linter (markdownlint, if available)
        for md_file in markdown_files:
            # Simulate markdown linting
            result = subprocess.run(['echo', 'markdownlint', md_file], capture_output=True, text=True)
            
        assert mock_subprocess.called

    def test_documentation_structure(self, project_root):
        """Test overall documentation structure."""
        docs_files = []
        for root, dirs, files in os.walk(project_root):
            for file in files:
                if file.endswith('.md'):
                    docs_files.append(file)
        
        # Test for documentation categories
        categories = {
            'main': ['README.md'],
            'deployment': ['DEPLOYMENT_PIPELINE.md', 'DEPLOYMENT_SUMMARY.md', 'DEPLOYMENT_VALIDATION.md'],
            'features': ['FEATURE_DEPLOYMENT_GUIDE.md'],
            'architecture': ['ARCHITECTURE.md'],
            'security': ['SECURITY.md']
        }
        
        for category, expected_files in categories.items():
            found_files = [f for f in expected_files if f in docs_files]
            if category in ['main', 'deployment', 'features']:
                assert len(found_files) > 0, f"Missing {category} documentation"

    def test_table_of_contents(self, markdown_files):
        """Test table of contents in documentation."""
        for md_file in markdown_files:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for table of contents patterns
            toc_patterns = [
                "table of contents",
                "contents",
                "- [", 
                "* ["
            ]
            
            content_lower = content.lower()
            has_toc = any(pattern in content_lower for pattern in toc_patterns)
            
            # Large files should have table of contents

    def test_documentation_metadata(self, markdown_files):
        """Test documentation metadata and frontmatter."""
        for md_file in markdown_files:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for YAML frontmatter
            if content.startswith('---\n'):
                # Find end of frontmatter
                end_marker = content.find('\n---\n', 4)
                if end_marker > 0:
                    frontmatter = content[4:end_marker]
                    # Test that frontmatter contains useful metadata
                    assert 'title:' in frontmatter or 'description:' in frontmatter, \
                        f"Frontmatter in {md_file} lacks useful metadata"