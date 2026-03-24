def run_pricing_strategy(product_name: str, base_cost: float, competitor_price: float):
    """
    Calculates optimal pricing strategies based on cost and competition.
    Returns a Markdown report.
    """
    print(f"💰 [SKILL: PRICING] Calculating for {product_name}...")
    
    # Strategy 1: Cost-Plus (Safe)
    cost_plus = base_cost * 1.5
    
    # Strategy 2: Penetration (Aggressive)
    penetration = competitor_price * 0.85
    
    # Strategy 3: Premium (Brand)
    premium = competitor_price * 1.2
    
    # Strategy 4: Psychological
    # Round to nearest .99
    psychological = int(cost_plus) + 0.99
    
    report = f"""
### 💰 Pricing Strategy Report: {product_name}
**Base Cost:** ${base_cost} | **Competitor:** ${competitor_price}

#### 📊 Recommended Strategies

| Strategy | Price | Margin | Rationale |
| :--- | :--- | :--- | :--- |
| **Cost-Plus (Safe)** | **${cost_plus:.2f}** | 33% | Guarantees profit. Good for MVP. |
| **Penetration** | **${penetration:.2f}** | {((penetration - base_cost)/penetration)*100:.1f}% | Undercuts market by 15%. Grabs share fast. |
| **Premium** | **${premium:.2f}** | {((premium - base_cost)/premium)*100:.1f}% | Positions as high-end. Requires strong branding. |
| **Psychological** | **${psychological}** | ~33% | Uses 'Left Digit Effect' to seem cheaper. |

#### 💡 AI Recommendation
"""
    if penetration < base_cost:
        report += "- ⚠️ **WARNING:** Penetration price is below cost! Do not use unless funded.\n"
        report += "- ✅ **Go with Cost-Plus** to ensure survival."
    elif premium > competitor_price * 1.5:
        report += "- ⚠️ **WARNING:** Premium is too high vs market. Risk of zero sales.\n"
        report += "- ✅ **Go with Psychological** pricing."
    else:
        report += "- ✅ **Balanced Approach:** Start with **Penetration** to get users, then raise to **Premium**."
        
    return report
