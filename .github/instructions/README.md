# Instructions Directory

This directory contains module-specific instructions for GitHub Copilot to understand the architecture and patterns of each component in the xSwE Agent project.

## Structure

Each file documents a specific module with:

- **Purpose**: What the module does
- **Key Components**: Main classes and interfaces
- **Patterns**: Design patterns used
- **Best Practices**: Guidelines and conventions
- **Testing**: Testing approaches
- **Examples**: Code snippets and usage patterns

## Files

### Core Modules

- **[analytics.md](./analytics.md)** - Analytics engine with strategy pattern for different analysis types
- **[github-monitor.md](./github-monitor.md)** - GitHub API integration with caching and rate limiting
- **[charts.md](./charts.md)** - Chart generation using matplotlib and plotly
- **[gemini-integration.md](./gemini-integration.md)** - Google Gemini AI integration for code analysis
- **[mcp-server.md](./mcp-server.md)** - FastAPI server with REST endpoints
- **[config.md](./config.md)** - Configuration management with Pydantic

## Usage

These instructions are automatically picked up by GitHub Copilot when working in the corresponding module directories. They provide context-specific guidance for:

- Code generation
- Pattern adherence
- Best practices
- Common pitfalls to avoid

## Main Instructions

The main project instructions are in `.github/copilot-instructions.md` at the repository root, which provides:

- Overall project architecture
- Code style standards
- Testing requirements
- Git workflow
- Development setup

## Updating

When adding new modules or making significant architectural changes:

1. Update the relevant module instruction file
2. Keep examples current with actual code
3. Document new patterns and best practices
4. Update the main copilot-instructions.md if needed
