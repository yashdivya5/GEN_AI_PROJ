PET_CARE_INSTRUCTION_PROMPT = """
You are an expert in pet care and veterinary guidance.

Generate {num_instructions} detailed pet care instructions for a {pet_type} regarding {issue}.
The tone should be {tone}.

For each instruction:
1. Provide a clear and concise title.
2. Explain the instruction in 2-3 sentences.
3. If follow-up instructions are included, provide a short recommendation for continued care.

The instructions should be practical, easy to follow, and aligned with veterinary best practices.
RESPOND ONLY WITH THE CARE INSTRUCTIONS AND NO OTHER TEXT.
"""

