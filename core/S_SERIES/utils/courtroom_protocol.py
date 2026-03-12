import json
from typing import Type, Any, Dict, Optional
from pydantic import BaseModel, ValidationError

class CourtroomProtocol:
    """
    Enterprise-Grade Adversarial Validation (The Courtroom).
    Uses the Cortex engine to orchestrate a Defender (Proposes extraction) 
    and a Skeptic (Critiques extraction against source), 
    ending with a Judge (Pydantic strict validation).
    """

    def __init__(self, cortex_instance):
        """
        Args:
            cortex_instance: An instance of Cortex (core.S_SERIES.cortex.Cortex)
        """
        self.cortex = cortex_instance

    async def execute(self, 
                      source_text: str, 
                      extraction_prompt: str, 
                      schema: Type[BaseModel], 
                      max_iterations: int = 2) -> Optional[Dict[str, Any]]:
        """
        Executes the Courtroom debate.
        
        Args:
            source_text: The raw text (e.g. PDF content).
            extraction_prompt: The instruction for the Defender.
            schema: The Pydantic schema to enforce the final output.
            max_iterations: Maximum debate loops to prevent infinite loops.
            
        Returns:
            Dict containing the validated data, or None if validation fails.
        """
        
        print("\n🏛️ [COURTROOM] Session started.")
        
        # 1. System Prompts
        defender_sys = (
            "You are the Defender. Your job is to extract exact financial data from the provided text "
            "based strictly on the prompt. You must return only a valid JSON object matching the requested schema. "
            "CRITICAL: Return a FLAT JSON object. Do not include any nested keys, wrappers, arrays, or titles. "
            "The root of the JSON must directly contain the exact keys from the schema. "
            "Do not include markdown blocks or any other text."
        )
        
        skeptic_sys = (
            "You are the Skeptic Auditor. Your job is to find flaws, hallucinations, or incorrect assumptions "
            "made by the Defender. Compare the Defender's JSON against the original source text. "
            "If the Defender is 100% correct, reply 'APPROVED'. "
            "If there are errors (e.g. wrong quarter, wrong metric, wrong format), reply with a list of EXACT errors."
        )
        
        # Initial Extraction (Defender)
        current_attempt_prompt = f"Source Text (Excerpt):\n{source_text[:80000]}\n\nTask: {extraction_prompt}\nReturn JSON strictly. MAKE SURE JSON IS FLAT."
        print("🧑‍⚖️ [COURTROOM] Defender proposing initial extraction...")
        defender_output = await self.cortex.ask_async(current_attempt_prompt, system_prompt=defender_sys)
        
        for iteration in range(max_iterations):
            print(f"🕵️ [COURTROOM] Skeptic auditing attempt {iteration + 1}...")
            
            # Skeptic Review
            audit_prompt = (
                f"Source Text:\n{source_text[:80000]}\n\n"
                f"Defender's JSON Output:\n{defender_output}\n\n"
                f"Task Requirements: {extraction_prompt}\n"
                "Review the JSON against the Source Text. Are the values accurate and the requirements met? "
                "Reply 'APPROVED' if perfect. Otherwise, list the specific errors."
            )
            
            audit_result = await self.cortex.ask_async(audit_prompt, system_prompt=skeptic_sys)
            
            if "APPROVED" in audit_result.upper() and "ERROR" not in audit_result.upper():
                print("✅ [COURTROOM] Skeptic Approved. Passing to Judge (Pydantic)...")
            else:
                print(f"❌ [COURTROOM] Skeptic Rejected: {audit_result.strip()}")
                
                if iteration < max_iterations - 1:
                    print("🧑‍⚖️ [COURTROOM] Defender correcting based on Skeptic's feedback...")
                    correction_prompt = (
                        f"{current_attempt_prompt}\n\n"
                        f"Your previous attempt was rejected. Auditor Feedback:\n{audit_result}\n\n"
                        "Please provide a corrected JSON."
                    )
                    defender_output = await self.cortex.ask_async(correction_prompt, system_prompt=defender_sys)
                    continue
                else:
                    print("⚠️ [COURTROOM] Max iterations reached without Skeptic approval. Proceeding to Judge anyway.")
                    
            # Judge (Pydantic Validation)
            try:
                # Try to clean the LLM output if it has markdown ticks
                clean_json = self.cortex.extract_json(defender_output, schema.model_json_schema())
                if not clean_json:
                    raise ValueError("Could not extract a valid JSON object from the response.")
                
                # Enforce schema
                validated_data = schema(**clean_json)
                print("👨‍⚖️ [COURTROOM] Judge (Pydantic): APPROVED. Format is strictly compliant.")
                return validated_data.model_dump()
                
            except ValidationError as e:
                print(f"👨‍⚖️ [COURTROOM] Judge (Pydantic): REJECTED due to strict type mismatch.\n{e}")
                if iteration < max_iterations - 1:
                    print("🧑‍⚖️ [COURTROOM] Defender correcting based on Judge's strict formatting rules...")
                    correction_prompt = (
                        f"{current_attempt_prompt}\n\n"
                        f"Your previous attempt failed strict validation. Error:\n{e}\n\n"
                        "Please provide a corrected JSON that EXACTLY matches the requested schema types."
                    )
                    defender_output = await self.cortex.ask_async(correction_prompt, system_prompt=defender_sys)
                else:
                    return None
            except Exception as e:
                print(f"👨‍⚖️ [COURTROOM] Judge Error: {e}")
                return None
                
        print("🛑 [COURTROOM] Failed to produce valid output within max iterations.")
        return None
