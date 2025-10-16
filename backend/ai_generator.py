import google.generativeai as genai
from typing import List, Optional, Dict, Any
import json

class AIGenerator:
    """Handles interactions with Google's Gemini API for generating responses"""

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to comprehensive tools for course information.

Available Tools:
1. **search_course_content** - Search within course materials for specific content
   - Use for questions about course topics, lessons, concepts, or detailed materials
   - Can filter by course name and lesson number
   - Returns relevant excerpts from course content

2. **get_course_outline** - Get complete course structure and outline
   - Use when users ask about course structure, outline, lesson list, or "what's in this course"
   - Returns course title, link, instructor, and complete list of lessons with their titles
   - Ideal for "show me the outline", "what lessons are covered", "course structure" questions

Tool Usage Guidelines:
- **One tool call per query maximum**
- Choose the appropriate tool based on the question type
- Synthesize tool results into accurate, fact-based responses
- If tool yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without using tools
- **Course content questions**: Use search_course_content tool
- **Course structure questions**: Use get_course_outline tool
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, tool usage explanations, or question-type analysis
 - Do not mention "based on the search results" or "using the tool"

All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""

    def __init__(self, api_key: str, model: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=model,
            system_instruction=self.SYSTEM_PROMPT
        )

        # Pre-build base generation config
        self.generation_config = {
            "temperature": 0,
            "max_output_tokens": 800,
        }

    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with optional tool usage and conversation context.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools

        Returns:
            Generated response as string
        """

        # Build context with history if available
        if conversation_history:
            full_query = f"Previous conversation:\n{conversation_history}\n\nCurrent question: {query}"
        else:
            full_query = query

        # Convert tools to Gemini format if provided
        gemini_tools = None
        if tools:
            gemini_tools = self._convert_tools_to_gemini_format(tools)

        # Create chat session
        chat = self.model.start_chat(history=[])

        # Generate response
        try:
            response = chat.send_message(
                full_query,
                generation_config=self.generation_config,
                tools=gemini_tools
            )

            # Check if model wants to use tools
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    # Check if this part is a function call
                    if hasattr(part, 'function_call') and part.function_call:
                        return self._handle_tool_execution(
                            chat,
                            response,
                            tool_manager
                        )

            # Return direct text response
            return response.text

        except Exception as e:
            return f"Error generating response: {str(e)}"

    def _convert_tools_to_gemini_format(self, anthropic_tools: List):
        """Convert Anthropic tool format to Gemini function declarations"""
        from google.generativeai.types import FunctionDeclaration, Tool

        function_declarations = []

        for tool in anthropic_tools:
            # Convert Anthropic tool schema to Gemini function declaration
            func_decl = FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters=tool["input_schema"]
            )
            function_declarations.append(func_decl)

        return [Tool(function_declarations=function_declarations)]

    def _handle_tool_execution(self, chat, initial_response, tool_manager):
        """
        Handle execution of tool calls and get follow-up response.

        Args:
            chat: The chat session
            initial_response: The response containing function calls
            tool_manager: Manager to execute tools

        Returns:
            Final response text after tool execution
        """
        function_calls = []

        # Extract all function calls
        for part in initial_response.candidates[0].content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                function_calls.append(part.function_call)

        # Execute tools and collect results
        function_responses = []

        for fc in function_calls:
            # Extract function name and arguments
            func_name = fc.name
            func_args = dict(fc.args)

            # Execute the tool
            try:
                result = tool_manager.execute_tool(func_name, **func_args)

                function_responses.append({
                    "name": func_name,
                    "response": {"result": result}
                })
            except Exception as e:
                function_responses.append({
                    "name": func_name,
                    "response": {"error": str(e)}
                })

        # Send function responses back to model
        try:
            # Build function response parts
            response_parts = []
            for fr in function_responses:
                response_parts.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=fr["name"],
                            response=fr["response"]
                        )
                    )
                )

            # Get final response
            final_response = chat.send_message(
                response_parts,
                generation_config=self.generation_config
            )

            return final_response.text

        except Exception as e:
            return f"Error processing tool results: {str(e)}"
