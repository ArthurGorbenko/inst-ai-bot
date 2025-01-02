const fixJSONPrompt = (inputString) => `
You are a highly skilled developer who can fix and reformat invalid JSON data into valid JSON.

I will provide you with a string that is supposed to represent JSON, but may contain syntax errors, missing quotes, extra commas, or other issues that prevent it from being parsed as valid JSON.

Your task:
1. Take the provided input string.
2. Correct any JSON formatting issues.
3. Return **only** the corrected, strictly valid JSON without any explanations, comments, or extra text.

Important details:
- Do not alter the keys or values unless you must adjust them for proper JSON formatting (e.g., adding missing quotes).
- Ensure that the final output can be directly parsed by \`JSON.parse()\` in JavaScript without errors.
- Output must be a single valid JSON object or array.

Here is the input:
\`\`\`
${inputString}
\`\`\`
`;

export default fixJSONPrompt;
