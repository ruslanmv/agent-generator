# src/agent_generator/utils/builder.py
import re
from pathlib import Path
import toml

from agent_generator.config import get_settings, Settings, SettingsError
from agent_generator.utils.prompts import render_prompt
from agent_generator.utils.parser import parse_natural_language_to_workflow
from agent_generator.frameworks import FRAMEWORKS
from agent_generator.providers import PROVIDERS
from agent_generator.utils.scaffold import (
    create_project_from_template,
    add_all_dependencies,
)


def _extract_code_block(llm_output: str) -> str:
    """
    Extract the first ```…``` fenced Python block if present,
    otherwise return the raw output stripped.
    """
    m = re.search(r"```(?:python)?\n(.+?)```", llm_output, re.S)
    return m.group(1).rstrip() if m else llm_output.strip()


def generate_agent_code_for_review(
    prompt: str,
    framework_name: str,
    provider_name: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    mcp: bool = False
) -> str:
    """
    Stage 1: replicate the CLI generate flow to produce clean Python code:
      1. Load defaults + overrides from Settings
      2. Parse NL → workflow
      3. Render the prompt template
      4. Call the LLM provider
      5. Generate code via the framework generator
      6. Strip fences and retry if truncated
    """
    # 1) Load and validate settings
    try:
        defaults = get_settings()
    except SettingsError as e:
        raise RuntimeError(f"Configuration error: {e}")

    provider_key = provider_name or defaults.provider
    settings = Settings(
        provider=provider_key,
        model=model or defaults.model,
        temperature=temperature if temperature is not None else defaults.temperature,
        max_tokens=max_tokens or defaults.max_tokens
    )

    # 2) Convert prompt into structured workflow
    workflow = parse_natural_language_to_workflow(prompt)

    # 3) Instantiate provider and framework generator
    provider_cls = PROVIDERS[provider_key]
    provider_inst = provider_cls(settings)
    framework_cls = FRAMEWORKS[framework_name]
    generator = framework_cls()

    # 4) Render prompt and invoke LLM
    #prompt_str = render_prompt(workflow, settings, framework_name)
    #provider_inst.generate(prompt_str)

    # 5) Produce the code artifact
    raw_code = generator.generate_code(workflow, settings, mcp=mcp)
    code = _extract_code_block(raw_code)

    # 6) If it looks truncated (no trailing newline), ask to continue
   # if not code.endswith("\n"):
   #     cont_prompt = prompt_str + "\n\nPlease continue the code."
   #     provider_inst.generate(cont_prompt)
   #     cont_raw = generator.generate_code(workflow, settings, mcp=mcp)
   #     code += "\n" + _extract_code_block(cont_raw)
   # if not code.endswith("\n"):
   #     # ask the FrameworkGenerator to continue the same prompt
   #     cont_raw = generator.generate_code(workflow, settings, mcp=mcp)
   #     code += "\n" + _extract_code_block(cont_raw)

    # Guarantee exactly one trailing newline
    if not code.endswith("\n"):
        code += "\n"


    return code


def build_accepted_project(
    project_name: str,
    framework_name: str,
    approved_code: str
):
    """
    Stage 2: scaffold a full project based on templates/<framework_name>,
    then inject all dependencies from its config.toml.
    """
    base = Path.cwd()
    tpl_dir = Path(__file__).parent / "templates" / framework_name
    config = toml.load(tpl_dir / "config.toml")

    print(f"🔨 Building project '{project_name}' ({framework_name})…")
    project_path = create_project_from_template(
        base_path=base,
        category=framework_name,
        project_name=project_name,
        author="AI Agent Generator",
        code_content=approved_code
    )

    add_all_dependencies(project_path, config)

    print(f"✅ Build complete!  cd {project_path} && make install && make run")
