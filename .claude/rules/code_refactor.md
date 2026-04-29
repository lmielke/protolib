---
script_path: /home/lars/repos/protolib/.claude/rules/code_refactor.md
purpose: "Refactor discipline for dead/unused code — reference-find workflow, safe renames, flag-before-delete, and minimal-context working rule."
description: "Applied during code-cleanup passes. Emphasises high-entropy search terms, scoped find commands, and preview-before-apply renames so broken references are caught before anything is deleted. Used by architect-implementer when structural moves are required."
update_rules: "Update requires explicit approval."
---

# Refactor

## Purpose
Remove dead / unused code while keeping dependencies intact.  
Work with **minimal context only** to avoid noise and wasted tokens.

---

## Core Rule
- Find all references before changing anything
- Change only what is necessary
- If unsure → flag, don’t delete

---



## 1. Find References (with context)
Use high entropy search terms (i.e. variable_name, file_name.ext) to limit result volume and increase relevance. Scope the search
to specific directories and exclude noise via shared session variables. Exclude irrelevant directories to reduce the search scope, limit search depth. 

```bash
# --- session setup (run at the beginning) ---
ignoreDirs=(.git __pycache__ .venv venv node_modules build dist .idea .mypy_cache)
fd_ignore_args=(); for d in "${ignoreDirs[@]}"; do fd_ignore_args+=(--exclude "$d"); done

# --- single term ---
printf "ignoreDirs:\n"; printf "  %s\n" "${ignoreDirs[@]}"
fdfind -t f . -e py -d 3 "${fd_ignore_args[@]}" -x grep -nH -C 3 "my_func" {}

# --- multiple terms (OR) ---
printf "ignoreDirs:\n"; printf "  %s\n" "${ignoreDirs[@]}"
terms=(my_func other_func third_term); pattern=$(IFS='|'; echo "${terms[*]}")
fdfind -t f . -e py -d 3 "${fd_ignore_args[@]}" -x grep -nH -C 3 -E "$pattern" {}

# --- same but using .fdignore (overrides array) ---
printf "ignoreDirs:\n"; printf "  %s\n" "${ignoreDirs[@]}"
fdfind -t f . -e py -d 3 --ignore-file .fdignore -x grep -nH -C 3 "my_func" {}
```

**Why this matters:**  
- `-C 3` → NOTE: use a number that suits the search width of your code (e.g. -/+ 3 lines)
- avoids opening full files  
- this is your **default command**
- ignore archive dirs and system files

---

## 2. Rename (safe, scoped)

```bash
# preview
fdfind -t f . -e py -x grep -nH "old_name" {}

# apply
fdfind -t f . -e py -x sed -i 's/\bold_name\b/new_name/g' {}
```

**Why split preview/apply:**  
- prevents blind global replacements  
- ensures you don’t break unrelated code

---

## 3. Flag Instead of Delete

```bash
fdfind -t f . -e py -x sed -i '/old_logic/s/^/# TODO_DELETE: /' {}
```

**Why:**  
- safe refactor step  
- lets you verify later before removal  

---

## Optional (only if needed)

```bash
# detect rule violation (missing *args)
fdfind -e py -x grep -nH '^\s*def [^(]*(\([^*]*\))' {}
```

Use this only when enforcing your Python rules.

---

## Workflow

1. Find usage  
2. Inspect context (no full file reads)  
3. Rename or flag  
4. Re-run search to confirm impact  

---

## Principle

Refactor =  
**find → verify → minimal change → re-check**

Anything else = unnecessary complexity