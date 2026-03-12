import re

def run_react_audit(code_snippet: str):
    """
    Analyzes React code for common anti-patterns.
    Returns a Markdown report.
    """
    print(f"⚛️ [SKILL: REACT-AUDIT] Analyzing Code...")
    
    issues = []
    score = 100
    
    # Check 1: Inline Styles
    if "style={{" in code_snippet:
        issues.append("🔴 **Inline Styles detected.** Use Tailwind classes or CSS modules for better performance.")
        score -= 20
        
    # Check 2: useEffect missing dependency array
    if re.search(r"useEffect\(\s*\(\)\s*=>\s*{[^}]*}\s*\)", code_snippet):
        issues.append("🔴 **useEffect missing dependency array.** This causes infinite loops.")
        score -= 30
        
    # Check 3: console.log left in code
    if "console.log" in code_snippet:
        issues.append("🟠 **console.log detected.** Remove debug logs before production.")
        score -= 10
        
    # Check 4: Any type
    if ": any" in code_snippet:
        issues.append("🟠 **Usage of 'any' type.** Defeats the purpose of TypeScript.")
        score -= 15

    report = f"""
### ⚛️ React Code Audit
**Quality Score: {score}/100**

#### 🔍 Issues Found
"""
    if issues:
        for issue in issues:
            report += f"- {issue}\n"
    else:
        report += "- ✅ **Clean Code!** No obvious anti-patterns found.\n"
        
    report += "\n#### 💡 Best Practices Guide\n"
    report += "- Use **Functional Components** with Hooks.\n"
    report += "- Prefer **Tailwind CSS** for styling.\n"
    report += "- Always define **Prop Types** or Interfaces.\n"
    
    return report
