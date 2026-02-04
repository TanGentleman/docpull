#!/usr/bin/env python3
"""Deploy docpull to Modal.

Usage: python deploy.py [--open-browser] [--json] [--skip-install]
"""

import argparse
import json
import re
import subprocess
import sys
import webbrowser
from pathlib import Path


def sanitize_app_name(name: str) -> str:
    """Sanitize app name for Modal (alphanumeric, hyphens, underscores only)."""
    sanitized = re.sub(r'[^a-zA-Z0-9-_]', '', name)
    return sanitized or "doc"

# Delimiters for managed zshrc section
ALIAS_START = "# >>> docpull alias >>>"
ALIAS_END = "# <<< docpull alias <<<"


def check_venv():
    """Verify environment is ready for deployment."""
    project_root = Path(__file__).parent
    venv_path = project_root / ".venv"

    if has_uv():
        print("✅ Using uv for dependency management")
        # uv will create/sync .venv automatically during install_requirements
        return

    # For non-uv users, check for existing venv
    venv_python = venv_path / "bin" / "python"

    if not venv_path.exists() or not venv_python.exists():
        print("⚠️  No virtual environment found at .venv/")
        try:
            response = input("   Create one now? [Y/n]: ").strip().lower()
        except EOFError:
            response = "n"

        if response in ("", "y", "yes"):
            print("\n🔧 Creating virtual environment...")
            result = subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"❌ Error creating virtual environment:")
                print(result.stderr)
                sys.exit(1)
            print("✅ Virtual environment created")
        else:
            print("\nTo create manually:")
            print(f"  python -m venv {venv_path}")
            print(f"  source {venv_path}/bin/activate")
            print("  pip install -e .")
            sys.exit(1)
    else:
        print("✅ Virtual environment detected")


def install_requirements():
    """Install Python dependencies."""
    print("\n📦 Installing dependencies...")

    project_root = Path(__file__).parent

    if has_uv():
        # uv sync creates .venv if needed and installs project + dependencies
        result = subprocess.run(
            ["uv", "sync"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        if result.returncode != 0:
            print("❌ Error running uv sync:")
            print(result.stderr)
            sys.exit(1)
    else:
        # For non-uv: use the project's venv Python for pip install
        venv_python = project_root / ".venv" / "bin" / "python"
        if not venv_python.exists():
            print("❌ Error: Virtual environment not found")
            print(f"Please create it first: python -m venv {project_root}/.venv")
            sys.exit(1)

        result = subprocess.run(
            [str(venv_python), "-m", "pip", "install", "-e", str(project_root)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("❌ Error installing dependencies:")
            print(result.stderr)
            sys.exit(1)

    print("✅ Dependencies installed")


def has_uv():
    """Check if uv is available on the system."""
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_modal_command():
    """Get the appropriate modal command prefix.

    Returns:
        list: Command prefix for running modal
    """
    project_root = Path(__file__).parent
    if has_uv():
        # Use --directory to ensure we're in the project context
        return ["uv", "run", "--directory", str(project_root), "modal"]
    else:
        # Use the project's venv Python directly (avoids activation issues)
        venv_python = project_root / ".venv" / "bin" / "python"
        if venv_python.exists():
            return [str(venv_python), "-m", "modal"]
        # Fallback to current Python
        return [sys.executable, "-m", "modal"]


def get_existing_apps(app_name: str):
    """Get list of existing Modal apps.

    Args:
        app_name: The app name to look for

    Returns:
        dict: Map of app description to app ID for docpull apps
    """
    try:
        modal_cmd = get_modal_command()
        result = subprocess.run(
            modal_cmd + ["app", "list", "--json"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return {}

        apps = json.loads(result.stdout)
        return {
            app["Description"]: app["App ID"]
            for app in apps
            if app["State"] == "deployed"
            and app["Description"] == app_name
        }
    except (json.JSONDecodeError, KeyError, FileNotFoundError):
        return {}


def deploy_api(app_name: str):
    """Deploy Modal API and extract URL.

    Args:
        app_name: The Modal app name

    Returns:
        str: API URL from deployment output
    """
    print("\n🚀 Deploying Modal API...")
    api_path = Path(__file__).parent / "api" / "server.py"

    if not api_path.exists():
        print(f"❌ Error: {api_path} not found")
        sys.exit(1)

    # Check for existing deployment
    existing_apps = get_existing_apps(app_name)
    if app_name in existing_apps:
        print(f"⚠️  Note: Redeploying existing app (ID: {existing_apps[app_name]})")

    modal_cmd = get_modal_command()
    result = subprocess.run(
        modal_cmd + ["deploy", str(api_path)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("❌ Error deploying API:")
        print(result.stderr)
        sys.exit(1)

    # Extract API URL from deployment output
    # Example: https://<workspace>--doc-pull.modal.run (APP_NAME=doc, function=pull)
    url_pattern = rf'https://[^\s]+--{app_name}-pull\.modal\.run'
    match = re.search(url_pattern, result.stdout)

    if not match:
        print("❌ Error: Could not extract API URL from deployment output")
        print("\nDeployment output:")
        print(result.stdout)
        print("\nSearching for URL pattern:", url_pattern)
        sys.exit(1)

    api_url = match.group(0)
    print(f"✅ API deployed: {api_url}")
    return api_url


def save_config(api_url: str, app_name: str, access_key: str | None = None):
    """Save configuration to .env file.

    Args:
        api_url: The Modal API URL to save
        app_name: The Modal app name
        access_key: Optional access key for API authentication
    """
    print("\n💾 Saving configuration...")
    env_path = Path(__file__).parent / ".env"

    lines = [
        "# Docpull configuration - auto-generated by deploy.py",
        "# Do not commit this file (it's in .gitignore)",
        "",
        f"APP_NAME={app_name}",
        f"SCRAPER_API_URL={api_url}",
    ]

    if access_key:
        lines.append(f"ACCESS_KEY={access_key}")

    env_content = "\n".join(lines) + "\n"

    try:
        env_path.write_text(env_content)
        print(f"✅ Configuration saved to {env_path}")
    except OSError as e:
        print(f"❌ Error saving configuration: {e}")
        sys.exit(1)



def setup_global_alias(skip_prompt=False):
    """Add global docpull alias to zshrc.

    Args:
        skip_prompt: If True, add alias without prompting (default behavior)

    Returns:
        bool: True if alias was added or already exists, False otherwise
    """
    project_dir = Path(__file__).parent.resolve()
    zshrc_path = Path.home() / ".zshrc"

    # Check if alias already exists
    if zshrc_path.exists():
        content = zshrc_path.read_text()
        if ALIAS_START in content:
            print("\n✅ Global docpull alias already configured in ~/.zshrc")
            return True

    if not skip_prompt:
        print("\n🔧 Setup global 'docpull' command?")
        print(f"   This will add an alias to ~/.zshrc pointing to {project_dir}/docpull")

        try:
            response = input("   Add global docpull command? [Y/n]: ").strip().lower()
        except EOFError:
            response = "n"

        if response not in ("", "y", "yes"):
            print("   Skipped. Use 'python -m cli.main' for local CLI access.")
            return False
    else:
        print(f"\n🔧 Adding global 'docpull' command to ~/.zshrc...")

    # Build the alias block
    alias_block = f"""\n{ALIAS_START}
alias docpull="{project_dir}/docpull"
{ALIAS_END}\n"""

    try:
        with open(zshrc_path, "a") as f:
            f.write(alias_block)
        print("   ✅ Added to ~/.zshrc")
        print("   Run 'source ~/.zshrc' or open a new terminal to use 'docpull'")
        return True
    except OSError as e:
        print(f"   ❌ Failed to update ~/.zshrc: {e}")
        return False


def display_summary(api_url, open_browser=False):
    """Display deployment summary.

    Args:
        api_url: The deployed API URL (also serves the UI at /)
        open_browser: Whether to open the URL in browser
    """
    print("\n" + "=" * 60)
    print("🎉 Deployment Complete!")
    print("=" * 60)
    print(f"\n🌐 URL:      {api_url}")
    print("\n📚 Next steps:")
    print("  - Open in browser for the UI")
    print("  - Test the API: curl " + api_url + "/health")
    print("  - Use the CLI: python -m cli.main sites")
    print("\n🛑 To stop deployments:")
    print("  python teardown.py")
    print("=" * 60)

    if open_browser:
        print("\n🌐 Opening in browser...")
        webbrowser.open(api_url)


def main():
    """Run the deployment process."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Deploy docpull to Modal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deploy.py                              # Deploy with defaults (app name: doc)
  python deploy.py --app-name myapp             # Custom app name
  python deploy.py --access-key secret123       # Enable API authentication
  python deploy.py --open-browser               # Deploy and open UI
        """
    )
    parser.add_argument(
        "--app-name",
        default="doc",
        help="Modal app name (default: doc). Affects the deployed URL.",
    )
    parser.add_argument(
        "--access-key",
        default=None,
        help="Access key for API authentication. If set, requests must include X-Access-Key header.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format (for programmatic use)",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the deployed UI in your browser after deployment",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip dependency installation (assumes already installed)",
    )
    parser.add_argument(
        "--no-alias",
        action="store_true",
        help="Skip adding global docpull alias to ~/.zshrc",
    )
    args = parser.parse_args()

    json_mode = args.json
    open_browser = args.open_browser
    skip_install = args.skip_install
    no_alias = args.no_alias
    app_name = sanitize_app_name(args.app_name)
    access_key = args.access_key

    if not json_mode:
        print("🔧 Docpull Deployment Setup")
        print("=" * 60)
        print(f"   App name: {app_name}")
        if access_key:
            print("   Access key: ****")

    # Write config BEFORE deploying (server.py reads .env at build time)
    env_path = Path(__file__).parent / ".env"
    pre_deploy_lines = [f"APP_NAME={app_name}"]
    if access_key:
        pre_deploy_lines.append(f"ACCESS_KEY={access_key}")
    env_path.write_text("\n".join(pre_deploy_lines) + "\n")

    try:
        # Step 1: Check virtual environment
        check_venv()

        # Step 2: Install dependencies (optional skip)
        if not skip_install:
            install_requirements()
        elif not json_mode:
            print("\n⏭️  Skipping dependency installation")

        # Step 3: Deploy API (also serves the UI)
        api_url = deploy_api(app_name)

        # Step 4: Save full configuration (including deployed URL)
        save_config(api_url, app_name, access_key)

        # Step 5: Setup global alias (by default, skip prompt)
        if not json_mode and not no_alias:
            setup_global_alias(skip_prompt=True)

        # Step 6: Display summary
        if json_mode:
            result = {
                "status": "success",
                "api_url": api_url,
                "app_name": app_name,
            }
            print(json.dumps(result))
        else:
            display_summary(api_url, open_browser=open_browser)

    except KeyboardInterrupt:
        print("\n\n⚠️  Deployment cancelled by user")
        sys.exit(130)
    except SystemExit as e:
        if json_mode and e.code != 0:
            result = {"status": "error", "error": "Deployment failed"}
            print(json.dumps(result))
        raise
    except Exception as e:
        if json_mode:
            result = {"status": "error", "error": str(e)}
            print(json.dumps(result))
        else:
            print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
