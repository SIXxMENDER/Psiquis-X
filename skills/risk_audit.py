def run_risk_audit(text_content: str):
    """
    Audits text for business and legal risks.
    Returns a Markdown report.
    """
    print(f"⚖️ [SKILL: RISK-AUDIT] Scanning text...")
    
    risks = []
    score = 100
    
    # Keywords to flag
    red_flags = [
        ("guarantee", "Promising results can lead to lawsuits."),
        ("100%", "Absolute claims are dangerous."),
        ("secret", "Implies hidden information."),
        ("hack", "Unprofessional terminology."),
        ("unlimited", "Resource risk."),
        ("crypto", "High volatility sector."),
        ("no risk", "False claim. All business has risk.")
    ]
    
    for word, reason in red_flags:
        if word in text_content.lower():
            risks.append(f"🔴 **'{word.upper()}'**: {reason}")
            score -= 15
            
    report = f"""
### ⚖️ Risk Audit Report
**Safety Score: {score}/100**

#### 🚩 Detected Risks
"""
    if risks:
        for risk in risks:
            report += f"- {risk}\n"
    else:
        report += "- ✅ **Safe Content.** No high-risk keywords detected.\n"
        
    if score < 70:
        report += "\n**VERDICT: ⛔ REJECTED. Too many risks.**"
    else:
        report += "\n**VERDICT: ✅ APPROVED. Proceed with caution.**"
        
    return report
