#!/usr/bin/env python3
import os
import sys
import re
import glob

def get_scratch_dir():
    return ".scratch"

def init_feature(slug, title):
    scratch = get_scratch_dir()
    feat_dir = os.path.join(scratch, slug)
    issues_dir = os.path.join(feat_dir, "issues")
    
    os.makedirs(issues_dir, exist_ok=True)
    
    prd_path = os.path.join(feat_dir, "PRD.md")
    if not os.path.exists(prd_path):
        with open(prd_path, "w") as f:
            f.write(f"# PRD: {title}\n\n## Problem Statement / Bug Description\n\n## Solution\n\n## User Stories / Requirements\n1. As an <Actor>, I want <Feature>, in order to achieve <Benefit>.\n\n## Technical Decisions\n- Affected Modules:\n- Technical Clarifications/Architectural Decisions:\n- API Contracts / Data Models:\n\n## Testing Decisions\n- Modules to Test:\n- Test Interfaces (Seams):\n\n## Out of Scope\n- [Things that are not part of this change request]\n")
    
    set_active(slug)
    print(f"Feature '{slug}' initialized.")

def get_active():
    active_file = os.path.join(get_scratch_dir(), "active-feature.txt")
    if not os.path.exists(active_file):
        print("ERROR: No active feature found.")
        sys.exit(1)
    with open(active_file, "r") as f:
        slug = f.read().strip()
        if not slug:
            print("ERROR: Active feature file is empty.")
            sys.exit(1)
        print(slug)
        return slug

def set_active(slug):
    os.makedirs(get_scratch_dir(), exist_ok=True)
    with open(os.path.join(get_scratch_dir(), "active-feature.txt"), "w") as f:
        f.write(slug)
    print(f"Active feature set to '{slug}'")

def get_issue_status(issue_path):
    if not os.path.exists(issue_path):
        return None
    with open(issue_path, "r") as f:
        for line in f:
            if line.startswith("Status:"):
                return line.split(":", 1)[1].strip()
    return None

def next_issue():
    slug = get_active()
    # Intercept stdout to not print slug
    # We'll just read it quietly for this command
    sys.stdout.flush()
    
    issues_dir = os.path.join(get_scratch_dir(), slug, "issues")
    if not os.path.exists(issues_dir):
        print(f"ERROR: Issues directory not found for feature '{slug}'")
        sys.exit(1)
    
    issues = sorted(glob.glob(os.path.join(issues_dir, "*.md")))
    
    for issue_path in issues:
        status = get_issue_status(issue_path)
        if status != "ready-for-agent":
            continue
            
        blocked = False
        with open(issue_path, "r") as f:
            for line in f:
                if line.startswith("Blocked by:"):
                    blockers_str = line.split(":", 1)[1].strip()
                    if blockers_str.lower() != "none" and blockers_str != "[]" and blockers_str != "":
                        nums = re.findall(r'\d+', blockers_str)
                        for num in nums:
                            blocker_path = os.path.join(issues_dir, f"{num.zfill(2)}-{slug}.md")
                            b_status = get_issue_status(blocker_path)
                            if b_status != "resolved":
                                blocked = True
                                break
                    break
        if not blocked:
            print(issue_path)
            return issue_path
            
    print("No unblocked ready-for-agent issues found.")
    sys.exit(1)

def update_issue(issue_path, new_status):
    if not os.path.exists(issue_path):
        print(f"ERROR: Issue {issue_path} not found.")
        sys.exit(1)
        
    with open(issue_path, "r") as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        if line.startswith("Status:"):
            lines[i] = f"Status: {new_status}\n"
            break
            
    with open(issue_path, "w") as f:
        f.writelines(lines)
    print(f"Updated {issue_path} to Status: {new_status}")

def complete():
    active_file = os.path.join(get_scratch_dir(), "active-feature.txt")
    if os.path.exists(active_file):
        os.remove(active_file)
        print("Active feature cleared.")
    else:
        print("No active feature to clear.")

def list_open_features():
    scratch = get_scratch_dir()
    open_features = []
    
    if not os.path.exists(scratch):
        return
        
    for item in os.listdir(scratch):
        feat_dir = os.path.join(scratch, item)
        if os.path.isdir(feat_dir):
            issues_dir = os.path.join(feat_dir, "issues")
            if os.path.exists(issues_dir):
                is_open = False
                for issue_file in glob.glob(os.path.join(issues_dir, "*.md")):
                    if get_issue_status(issue_file) != "resolved":
                        is_open = True
                        break
                if is_open:
                    open_features.append(item)
    
    for f in sorted(open_features):
        print(f)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: feature.py <command> [args]")
        sys.exit(1)
        
    cmd = sys.argv[1]
    
    # Simple hack to silence get_active() when called from next_issue
    if cmd == "next-issue":
        # Capture get_active internally without printing
        active_file = os.path.join(get_scratch_dir(), "active-feature.txt")
        if not os.path.exists(active_file):
            print("ERROR: No active feature found.")
            sys.exit(1)
        with open(active_file, "r") as f:
            slug = f.read().strip()
        # Override get_active to just return slug
        def get_active(): return slug
        next_issue()
        sys.exit(0)
    
    if cmd == "init" and len(sys.argv) == 4:
        init_feature(sys.argv[2], sys.argv[3])
    elif cmd == "get-active":
        get_active()
    elif cmd == "set-active" and len(sys.argv) == 3:
        set_active(sys.argv[2])
    elif cmd == "update-issue" and len(sys.argv) == 4:
        update_issue(sys.argv[2], sys.argv[3])
    elif cmd == "complete":
        complete()
    elif cmd == "list-open-features":
        list_open_features()
    else:
        print(f"Invalid command or arguments: {sys.argv}")
        sys.exit(1)
