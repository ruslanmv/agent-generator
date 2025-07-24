# src/agent_generator/utils/scaffold.py
# A professional, template-driven project scaffolder capable of handling complex directory trees.

import toml
from pathlib import Path

# --- Constants ---
TEMPLATES_DIR = Path(__file__).parent / "templates"

# --- Private Helper Functions ---

def _render_content(content: str, context: dict) -> str:
    """Replaces placeholders in a string with context values."""
    # Use .format_map to avoid errors if a placeholder is missing in the context
    return content.format_map(context)

def _scaffold_from_directory_tree(
    project_path: Path,
    template_dir: Path,
    context: dict,
):
    """
    Recursively copies a template directory, renders file content, and creates the project.
    This is done in two passes to ensure directories are created before files.
    """
    items = list(template_dir.glob("**/*"))

    # Pass 1: Create all directories
    for item in items:
        if item.is_dir():
            relative_path = item.relative_to(template_dir)
            dest_path = project_path / relative_path
            dest_path.mkdir(parents=True, exist_ok=True)

    # Pass 2: Create and render all files
    for item in items:
        if item.is_file():
            relative_path = item.relative_to(template_dir)
            dest_path = project_path / relative_path

            # Strip the .template suffix from the destination filename
            if str(dest_path).endswith(".template"):
                dest_path = dest_path.with_suffix("")

            template_content = item.read_text()
            rendered_content = _render_content(template_content, context)
            dest_path.write_text(rendered_content)
    
    # The generated code for watsonx is usually a set of YAML/config files,
    # so we write the "code_content" (e.g., a primary agent YAML) to a default file.
    if "code_content" in context and context["code_content"]:
         (project_path / "agents" / f"{context['project_name']}_agent.yaml").write_text(context["code_content"])

    print("   ✓ Successfully scaffolded project from directory tree.")


def _scaffold_simple(
    project_path: Path,
    context: dict,
):
    """Creates a simple `src/main.py` style project using the `_shared` templates."""
    src_path = project_path / "src"
    src_path.mkdir(parents=True, exist_ok=True)

    template_dir = TEMPLATES_DIR / "_shared"
    # Add our new pyproject.toml.template to the list of files to render
    files_to_render = {
        "Makefile": "Makefile.template",
        "Dockerfile": "Dockerfile.template",
        ".gitignore": "gitignore.template",
        "pyproject.toml": "pyproject.toml.template", # Render the TOML from a template
    }

    for dest_name, tmpl_name in files_to_render.items():
        tmpl_path = template_dir / tmpl_name
        if tmpl_path.exists():
            content = _render_content(tmpl_path.read_text(), context)
            (project_path / dest_name).write_text(content)

    # The generated code is passed in the context and written to main.py
    if "code_content" in context:
        (src_path / "main.py").write_text(context["code_content"])
        
    print("   ✓ Successfully scaffolded simple project.")


def add_all_dependencies(project_path: Path, config: dict):
    """
    Reads `[dependencies]` from config.toml and injects them into
    pyproject.toml or requirements.txt, depending on scaffold type.
    """
    deps = config.get("dependencies", {})
    if not deps:
        return

    # Case 1: Poetry-based project (simple scaffold)
    pyproject_path = project_path / "pyproject.toml"
    if pyproject_path.exists():
        data = toml.load(pyproject_path)
        # Ensure the dependencies section exists
        if "dependencies" not in data.get("tool", {}).get("poetry", {}):
            data["tool"]["poetry"]["dependencies"] = {}
        
        data["tool"]["poetry"]["dependencies"].update(deps)
        
        with pyproject_path.open("w") as f:
            toml.dump(data, f)
            
        print("   ✓ Injected Poetry dependencies.")
        return

    # Case 2: requirements.txt-based project (tree_copy scaffold)
    req_path = project_path / "requirements.txt"
    if req_path.exists():
        existing_content = req_path.read_text()
        dep_lines = [f"{pkg}{ver}" for pkg, ver in deps.items()]
        
        final_deps = existing_content.splitlines()
        for dep in dep_lines:
            if dep not in final_deps:
                final_deps.append(dep)
        req_path.write_text("\n".join(final_deps))
        print("   ✓ Appended requirements.txt dependencies.")

# --- Public API ---

def create_project_from_template(
    base_path: Path,
    category: str,
    project_name: str,
    author: str,
    code_content: str
) -> Path:
    """
    Generates a project by dynamically choosing a scaffolding method
    based on the framework’s config.toml.
    """
    project_path = base_path / "builds" / category / project_name
    if project_path.exists():
        raise FileExistsError(f"Project directory already exists: {project_path}")

    print(f"✨ Creating project '{project_name}' in category '{category}'...")
    
    config_path = TEMPLATES_DIR / category / "config.toml"
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file 'config.toml' not found for category '{category}'.")
        
    config = toml.load(config_path)
    scaffold_type = config.get("scaffold_type", "simple")
    print(f"   ✓ Loaded configuration for '{category}'. Scaffolding type: {scaffold_type}.")

    # Get the python version from the config, with a sensible default
    python_version = config.get("project", {}).get("python", "^3.11")

    context = {
        "project_name": project_name,
        "build_category": category,
        "author_name": author,
        "python_version": python_version,
        "code_content": code_content,
    }

    # First, create the file structure from templates
    if scaffold_type == "tree_copy":
        tree_dir = TEMPLATES_DIR / category / "project_template"
        if not tree_dir.is_dir():
            raise NotADirectoryError(f"The 'tree_copy' type requires a 'project_template' directory for '{category}'.")
        _scaffold_from_directory_tree(project_path, tree_dir, context)
    else:
        _scaffold_simple(project_path, context)

    # After creating files, add the dependencies
    add_all_dependencies(project_path, config)

    print(f"\n✅ Project '{project_name}' created successfully!")
    return project_path

__all__ = [
    "create_project_from_template",
    "add_all_dependencies",
]
