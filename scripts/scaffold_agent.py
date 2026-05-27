#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
import subprocess

def to_camel_case(s: str) -> str:
    parts = s.replace("-", " ").replace("_", " ").split()
    return "".join(p.capitalize() for p in parts)

def to_snake_case(s: str) -> str:
    return s.lower().replace("-", "_").replace(" ", "_")

def main():
    parser = argparse.ArgumentParser(
        description="Scaffold a premium, production-grade AI Agent with 8-layer security defense loops.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="The human-readable name of the agent (e.g. 'Market Assistant')"
    )
    parser.add_argument(
        "--dest",
        type=str,
        default=None,
        help="Target folder location (defaults to a snake_case directory in current folder)"
    )
    
    args = parser.parse_args()
    agent_name = args.name
    agent_snake = to_snake_case(agent_name)
    agent_camel = to_camel_case(agent_name)
    
    if not args.dest:
        dest_dir = os.path.abspath(agent_snake)
    else:
        dest_dir = os.path.abspath(args.dest)
        
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "templates", "production-agent"))
    
    print("=================================================================")
    print("🤖 Production AI Agent Scaffolder Engine")
    print("=================================================================")
    print(f"Agent Name:    {agent_name}")
    print(f"CamelCase:     {agent_camel}")
    print(f"snake_case:    {agent_snake}")
    print(f"Source Folder: {template_dir}")
    print(f"Target Folder: {dest_dir}")
    print("-----------------------------------------------------------------")
    
    if not os.path.exists(template_dir):
        print(f"❌ Error: Core templates folder not found at {template_dir}", file=sys.stderr)
        sys.exit(1)
        
    if os.path.exists(dest_dir):
        print(f"❌ Error: Target folder already exists at {dest_dir}. Choose a new destination.", file=sys.stderr)
        sys.exit(1)
        
    print("📂 [1/4] Copying boilerplate file structure...")
    try:
        shutil.copytree(template_dir, dest_dir)
        print("   ✅ Copy successful.")
    except Exception as e:
        print(f"❌ Failed to copy template: {str(e)}", file=sys.stderr)
        sys.exit(1)
        
    print("✏️  [2/4] Substituting template variable placeholders...")
    replacements = {
        "{{AGENT_NAME}}": agent_name,
        "{{AGENT_NAME_SNAKE}}": agent_snake,
        "{{AGENT_NAME_CAMEL}}": agent_camel
    }
    
    substitution_count = 0
    for root, dirs, files in os.walk(dest_dir):
        for file in files:
            # Skip binary image file
            if file.endswith(".jpg") or file.endswith(".png") or file.endswith(".ico"):
                continue
                
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                modified = content
                for key, val in replacements.items():
                    if key in modified:
                        modified = modified.replace(key, val)
                        substitution_count += 1
                        
                if modified != content:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(modified)
            except Exception as e:
                print(f"   ⚠️ Warning: Skip processing {file} due to {str(e)}")
                
    print(f"   ✅ Done. Replaced {substitution_count} variable placeholders.")
    
    print("🐙 [3/4] Initializing Git repository...")
    try:
        subprocess.run(["git", "init"], cwd=dest_dir, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "add", "."], cwd=dest_dir, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "commit", "-m", f"feat: initial scaffold for {agent_snake} using Production Agent Template"], cwd=dest_dir, check=True, stdout=subprocess.DEVNULL)
        print("   ✅ Git initialization complete.")
    except Exception as e:
        print(f"   ⚠️ Warning: Git setup failed: {str(e)}")
        
    print("💡 [4/4] Finishing up...")
    print("-----------------------------------------------------------------")
    print(f"🎉 Success! Agent '{agent_name}' compiled beautifully in:")
    print(f"   📂 {dest_dir}")
    print("\n👉 To run your new agent immediately:")
    print(f"   1. cd {os.path.relpath(dest_dir)}")
    print("   2. cp .env.example .env")
    print("   3. pip install -e .")
    print("   4. python app/main.py")
    print("=================================================================")

if __name__ == "__main__":
    main()
