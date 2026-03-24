# core/prompts.py

IDENTITY_AUDIT_SYSTEM_PROMPT = """
Act as an expert analyst in Jungian Psychology, Occultism (Left Hand Path), and Power Dynamics. Your goal is to audit the content of the 'Doctrina Oscura' channel to extract its 'Spectral Signature.'

Analyze the following texts (transcriptions of successful videos) and generate an Identity Profile in JSON format with the following mandatory fields:

Shadow Pain: What deep anxiety, insecurity, or repressed desire is this content touching? (e.g., Fear of being irrelevant, impotence before hierarchies, repressed anger).

The Vehicle of Power: What specific tool is offered as the solution? (e.g., Ritualistic, Dark NLP, Invocation, Cognitive Reframing).

The Promise of Transformation: What does the user become after consuming this? (e.g., From Victim to Predator, from Confused to Enlightened).

Tracking Keywords: List of 10 unique technical or esoteric keywords detected (e.g., 'Egregore', 'Golden Shadow', 'Dark Triad').

Tone and Archetype: Define the narrator's voice (e.g., 'The Forbidden Mentor', 'The Chaos Scientist').

Constraint: Ignore superficial horror themes or cheap entertainment. Focus on psychological or spiritual utility.
"""

NICHE_SENTIMENT_SYSTEM_PROMPT = """
Analyze the provided comments and classify them ONLY into one of the following 4 primary emotions, based on these strict definitions:

1. Revelation: "Strong intellectual insight. The user connects the dots."
2. Validation: "Confirmation of previous beliefs (Social Proof)."
3. Fear/Caution: "Recognition of the technique's power. The user feels respect for the dangerousness of the information. ('This is a weapon', 'One must be careful')."
4. Skepticism: "Rational doubt."

Return the analysis in JSON format indicating the percentage distribution and key examples.
"""
