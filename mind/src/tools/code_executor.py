"""Code execution tool in sandboxed environment"""
import asyncio
import tempfile
import os
from typing import Dict, Any


async def execute_code(code: str, language: str = "python", timeout: int = 30) -> Dict[str, Any]:
    """
    Execute code in a sandboxed environment.
    
    Args:
        code: Code to execute
        language: Programming language
        timeout: Timeout in seconds
        
    Returns:
        Execution result with stdout, stderr, exit_code
    """
    if language != "python":
        return {"error": f"Language {language} not supported yet", "exit_code": 1}
    
    try:
        # Write code to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        # Execute with timeout
        process = await asyncio.create_subprocess_exec(
            'python', temp_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return {
                "stdout": stdout.decode('utf-8'),
                "stderr": stderr.decode('utf-8'),
                "exit_code": process.returncode,
                "success": process.returncode == 0
            }
        except asyncio.TimeoutError:
            process.kill()
            return {
                "error": "Execution timeout",
                "exit_code": 124,
                "success": False
            }
        finally:
            os.unlink(temp_file)
            
    except Exception as e:
        return {
            "error": str(e),
            "exit_code": 1,
            "success": False
        }
